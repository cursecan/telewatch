import sys
import time
import schedule
import telepot
import requests, json, re
import telepot.helper
from pprint import pprint
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telepot.delegate import (
    per_chat_id, create_open, pave_event_space, include_callback_query_chat_id)

tele_records = telepot.helper.SafeDict()
TOKEN = '528057329:AAFBShP7yaoh2ZgOl0Fg4Fzipw1kYitx9Iw'
_URL = 'http://127.0.0.1:8000/api/'

def splitKeyboard(keyboard, q=2):
    return [keyboard[i*q:(i+1)*q] for i in range((len(keyboard)//q)+1)]

class Pulsabot(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(Pulsabot, self).__init__(*args, **kwargs)
        
        global tele_record
        if self.id in tele_records:
            self.auth, self.token_id, self.idpel, self.product, self._edit_msg_ident, self.edit_msg_info, self.keyboard, self.confirm = tele_records[self.id]
            self._editor = telepot.helper.Editor(self.bot, self._edit_msg_ident) if self._edit_msg_ident else None
            self.editor_info = telepot.helper.Editor(self.bot, self.edit_msg_info) if self.edit_msg_info else None

        else:
            self.token_id = None
            self.product = ''
            self.confirm = False
            self.idpel = ''
            self.auth = False

            self._editor = None
            self._edit_msg_ident = None

            self.editor_info = None
            self.edit_msg_info = None

            self.keyboard = []


    # MAIN MENU VIEW
    def _main(self):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='DATA & PULSA', callback_data='DAPUL'),
                ],
                [
                    InlineKeyboardButton(text='GAME ONLINE', callback_data='GAME'),
                ],
                [
                    InlineKeyboardButton(text='E-TRANSPORT', callback_data='ETRANS'),
                ]
            ]
        )
        self.keyboard = [keyboard]
        self.product = ''
        self.confirm = False

        try :
            text = self.bot.editMessageReplyMarkup(self._edit_msg_ident, reply_markup=keyboard)
        except :
            text = self.sender.sendMessage(
                '<strong>Daftar Produk Warungid</strong>\nSerasa Warung Milik Kamu Sendiri',
                reply_markup=keyboard,
                parse_mode='HTML'
            )

        self._editor = telepot.helper.Editor(self.bot, text)
        self._edit_msg_ident = telepot.message_identifier(text)


    # TOKEN VALIDATION
    def _getToken(self):
        if not self.auth:
            url = _URL + 'core/get-token/'
            payload = {
                'telegram': self.id
            }
            r = requests.post(url=url, data=json.dumps(payload), headers={'Content-Type':'application/json'})
            if r.status_code == requests.codes.ok:
                rson = r.json()
                self.auth = True
                self.token_id = 'Token ' + rson.get('key', '')
                return True

            self.sender.sendMessage(
                'Maaf Anda belum melakukan verifikasi ID Telegram, silahkan melakukan verifikasi dengan cara ketik <strong>#token[5 digit code]</strong> yang dikirim ke email terdaftar.\n\nContoh: #token12345',
                parse_mode='HTML'
            )
            return False
        


    # GET PULSA OPERATORS
    def _getPulsaOperator(self):
        url = _URL + 'pulsa/operator/'
        # try :
        r = requests.get(url=url, headers={'Authorization': self.token_id, 'Content-Type': 'application/json'})
        if r.status_code == requests.codes.ok:
            rson = r.json()
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=splitKeyboard(
                    [InlineKeyboardButton(text=i['operator'], callback_data='pulsa_op#' + str(i['id'])) for i in rson], 2
                ) + [[InlineKeyboardButton(text='BACK', callback_data='BACK')]]
                    
                
            )
            
            self.keyboard.append(keyboard)

            text = self.bot.editMessageReplyMarkup(self._edit_msg_ident, reply_markup=keyboard)
            self._editor = telepot.helper.Editor(self.bot, text)
            self._edit_msg_ident = telepot.message_identifier(text)   
        # except:
        #     pass


    # GET PULSA PRODUCT LIST
    def _getPulsaProduct(self, operator=''):
        url = _URL + 'pulsa/product/?op=' + str(operator)
        try :
            r = requests.get(url=url, headers={'Authorization': self.token_id, 'Content-Type': 'application/json'})
            if r.status_code == requests.codes.ok:
                rson = r.json()
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=splitKeyboard(
                        [InlineKeyboardButton(text=i['title'], callback_data='pulsa_prod#' + str(i['id'])) for i in rson]
                    ) + [[InlineKeyboardButton(text='BACK', callback_data='BACK')]]
                )
                
                self.keyboard.append(keyboard)

                text = self.bot.editMessageReplyMarkup(self._edit_msg_ident, reply_markup=keyboard)
                self._editor = telepot.helper.Editor(self.bot, text)
                self._edit_msg_ident = telepot.message_identifier(text)
        except:
            pass

    
    # GET PULSA DETAIL PRODUCT
    def _detailPulsa(self, product):
        url = _URL + 'pulsa/product/' + product + '/'
        self._cancel_last_info()

        try:
            r = requests.get(url=url, headers={'Authorization': self.token_id, 'Content-Type': 'application/json'})
            if r.status_code == requests.codes.ok:
                rson = r.json()

                text = self.sender.sendMessage('<strong>{}</strong>\n{}'.format(rson['description'], rson['addinfo']), parse_mode='HTML')
                
                self.product = 'pulsa#' + rson['product_code']

                self.editor_info = telepot.helper.Editor(self.bot, text)
                self.edit_msg_info = telepot.message_identifier(text)
        except:
            pass


    # POST PULSA
    def _postInPulsa(self, product_code, phone):
        url = _URL + 'pulsa/topup/'
        payload = {
            'product_code': product_code,
            'phone': phone,
        }
        try :
            r = requests.post(
                url = url,
                data = json.dumps(payload),
                headers = {'Authorization': self.token_id, 'Content-Type': 'application/json'}
            )
            if r.status_code == requests.codes.ok:
                rson = r.json()
                if rson['status']['code'] == '00':
                    self.sender.sendMessage(
                        'No. {}\nPembelian <strong>{}</strong> pada Nomor <strong>{}</strong> harga <strong>Rp {:0,.0f}</strong> sedang diproses.'.format(
                            rson['trx']['trx_code'], rson['product']['title'], rson['trx']['phone'], rson['product']['price']
                        ),
                        parse_mode='HTML',
                    )

                else : 
                    self.sender.sendMessage(
                        'Transaksi gagal.\n'+rson['status']['description']
                    )
            else :
                self.sender.sendMessage(
                    'Gagal diproses, harap masukan nomor anda dengan benar.'
                )
            
            self._cancel_last_button()
            self._main()
        
        except :
            pass

        finally :
            self.product = ''
            self.idpel = ''



    # GET GAME OPERATORS
    def _getGameOperator(self):
        url = _URL + 'game/operator/'
        try :
            r = requests.get(url=url, headers={'Authorization': self.token_id, 'Content-Type': 'application/json'})
            if r.status_code == requests.codes.ok:
                rson = r.json()
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=splitKeyboard(
                        [InlineKeyboardButton(text=i['operator'], callback_data='game_op#' + str(i['id'])) for i in rson]
                    )+ [[InlineKeyboardButton(text='BACK', callback_data='BACK')]]
                )
                
                self.keyboard.append(keyboard)

                text = self.bot.editMessageReplyMarkup(self._edit_msg_ident, reply_markup=keyboard)
                self._editor = telepot.helper.Editor(self.bot, text)
                self._edit_msg_ident = telepot.message_identifier(text)   
        except:
            pass


    # GET GAME PRODUCT LIST
    def _getGameProduct(self, operator=''):
        url = _URL + 'game/product/?op=' + str(operator)
        try :
            r = requests.get(url=url, headers={'Authorization': self.token_id, 'Content-Type': 'application/json'})
            if r.status_code == requests.codes.ok:
                rson = r.json()
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=splitKeyboard(
                        [InlineKeyboardButton(text=i['title'], callback_data='game_prod#' + str(i['id'])) for i in rson]
                    ) + [[InlineKeyboardButton(text='BACK', callback_data='BACK')]]
                )
                
                self.keyboard.append(keyboard)

                text = self.bot.editMessageReplyMarkup(self._edit_msg_ident, reply_markup=keyboard)
                self._editor = telepot.helper.Editor(self.bot, text)
                self._edit_msg_ident = telepot.message_identifier(text)
        except:
            pass


    # GET GAME DETAIL PRODUCT
    def _detailGame(self, product):
        url = _URL + 'game/product/' + product + '/'
        self._cancel_last_info()

        try:
            r = requests.get(url=url, headers={'Authorization': self.token_id, 'Content-Type': 'application/json'})
            if r.status_code == requests.codes.ok:
                rson = r.json()

                text = self.sender.sendMessage('<strong>{}</strong>\n{}'.format(rson['description'], rson['addinfo']), parse_mode='HTML')
                
                self.product = 'game#' + rson['product_code']

                self.editor_info = telepot.helper.Editor(self.bot, text)
                self.edit_msg_info = telepot.message_identifier(text)
        except:
            pass


    # POST GAME
    def _postInGame(self, product_code, phone):
        url = _URL + 'game/topup/'
        payload = {
            'product_code': product_code,
            'phone': phone,
        }
        try :
            r = requests.post(
                url = url,
                data = json.dumps(payload),
                headers = {'Authorization': self.token_id, 'Content-Type': 'application/json'}
            )
            if r.status_code == requests.codes.ok:
                rson = r.json()
                if rson['status']['code'] == '00':
                    self.sender.sendMessage(
                        'No. {}\nPembelian <strong>{}</strong> pada Nomor <strong>{}</strong> harga <strong>Rp {:0,.0f}</strong> sedang diproses.'.format(
                            rson['trx']['trx_code'], rson['product']['title'], rson['trx']['phone'], rson['product']['price']
                        ),
                        parse_mode='HTML',
                    )

                else : 
                    self.sender.sendMessage(
                        'Transaksi gagal.\n'+rson['status']['description']
                    )
            else :
                self.sender.sendMessage(
                    'Gagal diproses, harap masukan nomor anda dengan benar.'
                )
            
            self._cancel_last_button()
            self._main()
        
        except :
            pass

        finally :
            self.product = ''
            self.idpel = ''



    # GET TRANSPORT OPERATORS
    def _getTransportOperator(self):
        url = _URL + 'transport/operator/'
        try :
            r = requests.get(url=url, headers={'Authorization': self.token_id, 'Content-Type': 'application/json'})
            if r.status_code == requests.codes.ok:
                rson = r.json()
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=splitKeyboard(
                        [InlineKeyboardButton(text=i['operator'], callback_data='transport_op#' + str(i['id'])) for i in rson]
                    )+ [[InlineKeyboardButton(text='BACK', callback_data='BACK')]]
                )
                
                self.keyboard.append(keyboard)

                text = self.bot.editMessageReplyMarkup(self._edit_msg_ident, reply_markup=keyboard)
                self._editor = telepot.helper.Editor(self.bot, text)
                self._edit_msg_ident = telepot.message_identifier(text)   
        except:
            pass


    # GET TRANSPORT PRODUCT LIST
    def _getTransportProduct(self, operator=''):
        url = _URL + 'transport/product/?op=' + str(operator)
        try :
            r = requests.get(url=url, headers={'Authorization': self.token_id, 'Content-Type': 'application/json'})
            if r.status_code == requests.codes.ok:
                rson = r.json()
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=splitKeyboard(
                        [InlineKeyboardButton(text=i['title'], callback_data='transport_prod#' + str(i['id'])) for i in rson]
                    ) + [[InlineKeyboardButton(text='BACK', callback_data='BACK')]]
                )
                
                self.keyboard.append(keyboard)

                text = self.bot.editMessageReplyMarkup(self._edit_msg_ident, reply_markup=keyboard)
                self._editor = telepot.helper.Editor(self.bot, text)
                self._edit_msg_ident = telepot.message_identifier(text)
        except:
            pass


    # GET TRANSPORT DETAIL PRODUCT
    def _detailTransport(self, product):
        url = _URL + 'transport/product/' + product + '/'
        self._cancel_last_info()

        try:
            r = requests.get(url=url, headers={'Authorization': self.token_id, 'Content-Type': 'application/json'})
            if r.status_code == requests.codes.ok:
                rson = r.json()

                text = self.sender.sendMessage('<strong>{}</strong>\n{}'.format(rson['description'], rson['addinfo']), parse_mode='HTML')
                
                self.product = 'transport#' + rson['product_code']

                self.editor_info = telepot.helper.Editor(self.bot, text)
                self.edit_msg_info = telepot.message_identifier(text)
        except:
            pass


    # POST TRANSPORT
    def _postInTransport(self, product_code, phone):
        url = _URL + 'transport/topup/'
        payload = {
            'product_code': product_code,
            'phone': phone,
        }
        try :
            r = requests.post(
                url = url,
                data = json.dumps(payload),
                headers = {'Authorization': self.token_id, 'Content-Type': 'application/json'}
            )
            if r.status_code == requests.codes.ok:
                rson = r.json()
                if rson['status']['code'] == '00':
                    self.sender.sendMessage(
                        'No. {}\nPembelian <strong>{}</strong> pada Nomor <strong>{}</strong> harga <strong>Rp {:0,.0f}</strong> sedang diproses.'.format(
                            rson['trx']['trx_code'], rson['product']['title'], rson['trx']['phone'], rson['product']['price']
                        ),
                        parse_mode='HTML',
                    )

                else : 
                    self.sender.sendMessage(
                        'Transaksi gagal.\n'+rson['status']['description']
                    )
            else :
                self.sender.sendMessage(
                    'Gagal diproses, harap masukan nomor anda dengan benar.'
                )
            
            self._cancel_last_button()
            self._main()
        
        except :
            pass

        finally :
            self.product = ''
            self.idpel = ''

    # DELETE/MOD LAST INFO TEXT
    def _cancel_last_info(self):
        if self.editor_info:
            self.editor_info.deleteMessage()
            self.editor_info = None
            self.edit_msg_info = None

    
    # DELETE/MOD LAST BUTTON MENU
    def _cancel_last_button(self):
        if self._editor:
            self._editor.editMessageReplyMarkup(reply_markup=None)
            self._editor = None
            self._edit_msg_ident = None

    
    # GO TO BACK / PREV MENU
    def return_back(self, keyboard):
        self.keyboard.pop()
        text = self.bot.editMessageReplyMarkup(self._edit_msg_ident, reply_markup=self.keyboard[-1])
        self._editor = telepot.helper.Editor(self.bot, text)
        self._edit_msg_ident = telepot.message_identifier(text)
        self.product = ''


    # PRE TOPUP VALIDATION
    def postValidation(self, text):
        self.idpel = text
        text = self.sender.sendMessage(
            'Lanjutkan transaksi? (<strong>Ya</strong> / <strong>Tidak</strong>)\nNo.Pel <strong>{}</strong>'.format(self.idpel),
            reply_markup = ReplyKeyboardMarkup(
                keyboard = [
                    [
                        KeyboardButton(text='Ya'),
                        KeyboardButton(text='Tidak')
                    ],
                ],
                one_time_keyboard = True,
                resize_keyboard = True,
            ),
            parse_mode = 'HTML',
            # reply_to_message_id = self.edit_msg_info[1]
        )

    def _getStartChat(self):
        self.sender.sendMessage(
            '<strong>Selamat Datang di Telegram Bot @warungid_bot</strong>\nKunjungi Website kami di <a href="http://warungid.com">Warungid.com</a> untuk informasi lebih lanjut.',
            parse_mode='HTML',
            reply_markup=ReplyKeyboardMarkup(
                keyboard = [
                    [
                        KeyboardButton(text='/menu')
                    ],
                ],
                one_time_keyboard = True,
                resize_keyboard = True,
            )
        )


    # SITE STATUS IN ACTIVE OR MAINTENANCE
    def _getSiteActive(self):
        url = _URL + 'core/site/1/'
        r = requests.get(url=url, headers={'Content-Type': 'application/json'})
        if r.status_code == requests.codes.ok:
            rson = r.json()
            if rson['status'] == True:
                return True
        return False

    def _postValidateTele(self, pin):
        keyboard = ReplyKeyboardMarkup(
            keyboard = [
                [
                    KeyboardButton(text='/menu')
                ]
            ],
            one_time_keyboard = True,
            resize_keyboard = True,
        )
        url = _URL + 'core/telegram/create/'
        payload = {
            'pin': pin,
            'telegram': self.id
        }
        r = requests.post(url=url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        if r.status_code == requests.codes.created:
            self.sender.sendMessage(
                'Validasi Sukses.\nID Telegram Anda telah terverifikasi, jaga kerahasiaan Telegram Anda agar tidak disalahgunakan oleh oknum tidak bertanggungjawab.\n\n~Warungid',
                reply_markup = keyboard
            )
        elif r.status_code == 204:
            self.sender.sendMessage(
                'Telegram Anda telah terverifikasi.',
                reply_markup = keyboard
            )
        else :
            self.sender.sendMessage(
                'Validasi Gagal, harap masukan token dengan benar.\nContoh: #token[12345]'
            )

    # MAIN CHAT MODUL
    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            if not self._getSiteActive():
                self.sender.sendMessage(
                    'SERVER MAINTENANCE\n\n<i>Mohon maaf server saat ini sedang dalam maintenance mohon tunggu beberapa saat lagi. Terimakasih</i>',
                    parse_mode='HTML',
                )
                self.confirm = False
                self.product = ''
                self.idpel = ''
                self._main()
                return

            if 'pulsa' in self.product :
                if msg['text'] == 'Ya' and self.idpel != '':
                    self.confirm = True
                    prod, code = self.product.split('#')
                    self._postInPulsa(code, self.idpel)
                    return

                elif msg['text'] == 'Tidak' and self.idpel != '' :
                    self.confirm = False
                    self.product = ''
                    self.idpel = ''
                    self.sender.sendMessage(
                        'Permintaan Anda telah dibatalkan.\n<strong>Ketik</strong> /menu untuk kembali ke menu utama.',
                        parse_mode = 'HTML'
                    )
                    self._main()
                    return

                self.postValidation(msg['text'])
                return

            if 'game' in self.product :
                if msg['text'] == 'Ya' and self.idpel != '':
                    self.confirm = True
                    prod, code = self.product.split('#')
                    self._postInGame(code, self.idpel)
                    return

                elif msg['text'] == 'Tidak' and self.idpel != '' :
                    self.confirm = False
                    self.product = ''
                    self.idpel = ''
                    self.sender.sendMessage(
                        'Permintaan Anda telah dibatalkan.\n<strong>Ketik</strong> /menu untuk kembali ke menu utama.',
                        parse_mode = 'HTML'
                    )
                    self._main()
                    return

                self.postValidation(msg['text'])
                return

            if 'transport' in self.product :
                if msg['text'] == 'Ya' and self.idpel != '':
                    self.confirm = True
                    prod, code = self.product.split('#')
                    self._postInTransport(code, self.idpel)
                    return

                elif msg['text'] == 'Tidak' and self.idpel != '' :
                    self.confirm = False
                    self.product = ''
                    self.idpel = ''
                    self.sender.sendMessage(
                        'Permintaan Anda telah dibatalkan.\n<strong>Ketik</strong> /menu untuk kembali ke menu utama.',
                        parse_mode = 'HTML'
                    )
                    self._main()
                    return

                self.postValidation(msg['text'])
                return
            
            
            if msg['text'] == '/menu':
                if not self.auth:
                    auth = self._getToken()
                    if not auth:
                        return
                self._cancel_last_button()
                self._main()
                return
            
            if msg['text'] == '/start':
                self._getStartChat()
                return

            if '#token' in msg['text'] :
                code = re.sub(r'#token', '', msg['text'])
                self._postValidateTele(code)
                return


    
    # CALLBACK
    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        self.bot.answerCallbackQuery(query_id, text='Ok. Transaction will be procces.')

        # BACK PROCESS
        if query_data == 'BACK':
            self.return_back(self.keyboard)
            return

        # PULSA DATA
        if query_data == 'DAPUL':
            self._getPulsaOperator()
            return

        # GAME
        if query_data == 'GAME':
            self._getGameOperator()
            return

        # TRANSPORT
        if query_data == 'ETRANS':
            self._getTransportOperator()
            return

        # OPERATOR PULSA
        if 'pulsa_op' in query_data:
            op, ids = query_data.split('#')
            self._getPulsaProduct(ids)
            return

        # OPERATOR GAME
        if 'game_op' in query_data:
            op, ids = query_data.split('#')
            self._getGameProduct(ids)
            return

        # OPERATOR TRANSPORT
        if 'transport_op' in query_data:
            op, ids = query_data.split('#')
            self._getTransportProduct(ids)
            return
        
        # PRODUCT PULSA
        if 'pulsa_prod' in query_data:
            prod, ids = query_data.split('#')
            self._detailPulsa(ids)
            return

        # PRODUCT GAME
        if 'game_prod' in query_data:
            prod, ids = query_data.split('#')
            self._detailGame(ids)
            return

        # PRODUCT TRANSPORT
        if 'transport_prod' in query_data:
            prod, ids = query_data.split('#')
            self._detailTransport(ids)
            return

    def on_close(self, ex):
        global tele_records
        tele_records[self.id] = (self.auth, self.token_id, self.idpel, self.product, self._edit_msg_ident, self.edit_msg_info, self.keyboard, self.confirm)



def getMessagePost():
    url = _URL + 'core/message/'
    r = requests.get(url=url, headers={'Content-Type':'application/json'})
    payload = {
        'closed': True
    }
    if r.status_code == requests.codes.ok:
        rjson = r.json()
        for msg in rjson:
            msgid = msg['id']
            subject = msg['subject']
            message = msg['message']
            r = requests.put(url=url+str(msgid)+'/', data=json.dumps(payload), headers={'Content-Type':'application/json'})
            for user_tel in msg['send_to']:
                try :
                    bot.sendMessage(
                        user_tel['teleid'],
                        '<b>{0}</b>\n\n{1}\n\n<i>Salam, Warungid.com</i>'.format(subject, message),
                        parse_mode = 'HTML'
                    )
                except :
                    pass


bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        pave_event_space())(
            per_chat_id(types=['private']), create_open, Pulsabot, timeout=10),
])
MessageLoop(bot).run_as_thread()
print('Listening ...')


schedule.every(5).seconds.do(getMessagePost)

while 1:
    schedule.run_pending()
    time.sleep(1)