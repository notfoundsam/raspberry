from __future__ import print_function
import sys, os
from .models import Remote, Button
from app import so, db
import uuid
from datetime import datetime

class RemoteControl:
    """docstring for RemoteControl"""
    def create(self, rc_type, rc_name, rc_icon, rc_order = 1, public = True):
        rc_id = "RC_" + str(uuid.uuid4()).replace('-', '_')

        if rc_type and rc_name and rc_icon:
            remote = Remote(remote_type = rc_type,
                            identificator = rc_id,
                            name = rc_name,
                            icon = rc_icon,
                            order = rc_order,
                            public = public,
                            timestamp = datetime.utcnow())

            db.session.add(remote)
            db.session.commit()
            # print('create remote type:%s' % type, file=sys.stderr)
            return True

    def addBtnToRemote(self, content):
        btn_id = "BTN_" + str(uuid.uuid4()).replace('-', '_')
        print(content['rc_id'], file=sys.stderr)

        rc = Remote.query.filter_by(identificator = content['rc_id']).first()

        # print(rc, file=sys.stderr)

        if rc is not None:
            btn = Button(identificator = btn_id,
                        name = content['btn_name'],
                        order_hor = content['btn_order_hor'],
                        order_ver = content['btn_order_ver'],
                        color = content['btn_color'],
                        signal = content['signal'],
                        remote_id = rc.id,
                        timestamp = datetime.utcnow())

            db.session.add(btn)
            db.session.commit()
            print('create btn: %s' % btn_id, file=sys.stderr)
            return True

    def removeBtnFromRemote(self, content):
        ids = content['buttons']

        for button in ids:
            btn = Button.query.filter_by(identificator = button).first()
            db.session.delete(btn)

        db.session.commit()

    def getRemotesList(self):
        remotes = []

        for remote in Remote.query.order_by(Remote.id).all():
            r = {'identificator': remote.identificator,
                'name': remote.name,
                'type': remote.remote_type,
                'icon': remote.icon}

            remotes.append(r)

        return remotes

    def getRemoteButtons(self, rc_id):
        buttons = []

        rc = Remote.query.filter_by(identificator = rc_id).first()

        if rc is not None:
            for button in rc.buttons.order_by(Button.order_ver.asc(), Button.order_hor.asc()).all():
                btn = {'identificator': button.identificator,
                        'name': button.name,
                        'color': button.color,
                        'order_ver': button.order_ver,
                        'order_hor': button.order_hor}

                buttons.append(btn)

        return buttons

    def regenerateLircCommands(self):
        print('---ENTER---', file=sys.stderr)

        ir_remotes = Remote.query.filter_by(remote_type = 'ir_rc').all()

        if ir_remotes is not None:
            print('---RC START---', file=sys.stderr)
            with open("ir_tmp_code.txt", "w") as text_file:

                for rc in ir_remotes:
                    buttons = rc.buttons.all()

                    if buttons:
                        text_file.write("begin remote\n")
                        text_file.write("\n")
                        text_file.write("name %s\n" % rc.identificator)
                        text_file.write("flags RAW_CODES\n")
                        text_file.write("eps 30\n")
                        text_file.write("aeps 100\n")
                        text_file.write("\n")
                        text_file.write("ptrail 0\n")
                        text_file.write("repeat 0 0\n")
                        text_file.write("gap 108000\n")
                        text_file.write("\n")
                        text_file.write("begin raw_codes\n")

                        for button in buttons:
                            text_file.write("  name %s\n" % button.identificator)
                            text_file.write("    %s\n" % button.signal)

                        text_file.write("end raw_codes\n")
                        text_file.write("\n")
                        text_file.write("end remote\n")
                        text_file.write("\n")

            print('---RC END---', file=sys.stderr)

    def addTestSignal(self, test_signal):
        with open('ir_tmp_code.txt', 'a') as text_file:
            text_file.write("begin remote\n")
            text_file.write("\n")
            text_file.write("name test\n")
            text_file.write("flags RAW_CODES\n")
            text_file.write("eps 30\n")
            text_file.write("aeps 100\n")
            text_file.write("\n")
            text_file.write("ptrail 0\n")
            text_file.write("repeat 0 0\n")
            text_file.write("gap 108000\n")
            text_file.write("\n")
            text_file.write("begin raw_codes\n")

            text_file.write("  name test_signal\n")
            text_file.write("    %s\n" % test_signal)

            text_file.write("end raw_codes\n")
            text_file.write("\n")
            text_file.write("end remote\n")

    def sendTestSignal(self):
        if 'APP_ENV' in os.environ and os.environ['APP_ENV'] == 'development':
            print('--- Sending test signal ---', file=sys.stderr)
            print("irsend SEND_ONCE %s %s" % ('test', 'test_signal'), file=sys.stderr)
        else:
            os.system("irsend SEND_ONCE %s %s" % ('test', 'test_signal'))

    def sendLircCommand(self, rc_id, btn_id):
        if 'APP_ENV' in os.environ and os.environ['APP_ENV'] == 'development':
            print('--- Sending command ---', file=sys.stderr)
            print(rc_id, file=sys.stderr)
            print(btn_id, file=sys.stderr)
        else:
            os.system("irsend SEND_ONCE %s %s" % (rc_id, btn_id))


    def reloadLirc(self):
        if 'APP_ENV' in os.environ and os.environ['APP_ENV'] == 'development':
            print('--- Lirc config reloaded ---', file=sys.stderr)
        else:
            os.system("sudo /etc/init.d/lircd stop")
            os.system("sudo cp ir_tmp_code.txt /etc/lirc/lircd.conf")
            os.system("sudo /etc/init.d/lircd start")


        