import sys
import time
import telepot
from telepot.loop import MessageLoop
from decouple import config

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    if content_type == 'text':
        bot.sendMessage(
            chat_id,
            'SERVER MAINTENANCE\n\n<i>Mohon maaf atas ketidaknyamananya karena saat ini server sedang dalam proses maintenance. Terimakasih</i>',
            parse_mode = 'HTML'    
        )

TOKEN = '528057329:AAFBShP7yaoh2ZgOl0Fg4Fzipw1kYitx9Iw'

bot = telepot.Bot(TOKEN)
MessageLoop(bot, handle).run_as_thread()
print ('Listening ...')

# Keep the program running.
while 1:
    time.sleep(10)