from alert import BaseAlert
from dot3k import lcd, backlight

class dot3k(BaseAlert):
    def ready(self):
        lcd.clear()
        backlight.rgb(0,0,0)
        backlight.rgb(255,255,255)
        lcd.write("Ready!")

    def clear(self):
        lcd.clear()
        backlight.rgb(0,0,0)
        lcd.write("...")

    def info(self, message):
        lcd.clear()
        backlight(255,255,255)
        lcd.write(message.body)

    def warning(self, message):
        print("here i am")
        lcd.clear()
        backlight.rgb(255,0,0)
        lcd.write(message.body)

    def display_message(self, message):
        lcd.clear()

        if message.warning is True:
            backlight.rgb(255,0,0)
        else:
            backlight.rgb(255,255,255)

        lcd.set_cursor_position(0,0)
        lcd.write("%s / %s" % (self.message_count, self.get_runtime()))
        lcd.set_cursor_position(0,1)
        lcd.write(message.title)
        lcd.set_cursor_position(0,2)
        lcd.write(message.data)

