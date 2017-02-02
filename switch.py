#!/usr/bin/python3
import serial
from PyQt5 import QtCore, QtGui, QtWidgets
from gui import Ui_Modem3GSwitcher
import sys
import serial
from serial import Serial
from serial.serialutil import SerialException
import time

class Main( Ui_Modem3GSwitcher ):

	found_modem = False
	usb_ports = '/dev/ttyUSB'
	usb_port = ''

	def __init__( self, dialog ):
		super( self.__class__, self ).__init__()
		self.setupUi( dialog )
		self.serial = None

		self.checkpushButton.clicked.connect( self.check )
		self.mode.setEnabled( False )
		self.applyButton.setEnabled( False )

		self.applyButton.clicked.connect( self.change_mode )

		self.network_commands = [ '2,1,3FFFFFFF,2,4', '2,2,3FFFFFFF,2,4', '13,1,3FFFFFFF,2,4', '14,2,3FFFFFFF,2,4' ]

		for i in range( 0, 5 ):
			if not self.found_modem:
				self.usb_port = str( self.usb_ports ) + str( i )
				self.check( self.usb_port )
			else:
				break
		if self.found_modem:
			self.Port.setText( self.usb_port )

	def check( self, port = False ):
		if port is False:
			port = self.Port.text()
		try:
			self.Serial = Serial( port )
			if not self.Serial.is_open:
				self.Serial.open()
			details = self.extract_details( self.send_command( 'ATI' ) )
			if details:
				self.found_modem = True
				self.errLabel.setText( '' )
				self.mode.setEnabled( True )
				self.applyButton.setEnabled( True )
				self.manu_label.setText( details[ 'Manufacturer' ] )
				self.model_label.setText( details[ 'Model' ] )
				self.firmware_label.setText( details[ 'Revision' ] )
				self.imei_label.setText( details[ 'IMEI' ] )
				self.show_status()
		except SerialException as err:
			self.errLabel.setText( err.args[ 1 ] )

	def show_status( self ):
		command = self.send_command( 'AT^SYSINFO' )
		if command:
			command = command.split( ':' )[ 1 ].strip( 'OK\r\n')
			command = command.split( ',' )
			if command[ 3 ] == '3':
				self.status_label.setText( '2G/EDGE' )
			elif command[ 3 ] == '5':
				self.status_label.setText( '3G/WCDMA' )
			elif command[ 3 ] == '7':
				self.status_label.setText( '2G/3G' )
			elif command[ 3 ] == '0':
				self.status_label.setText( 'No Service' )
			else:
				self.status_label.setText( 'Unknown' )

	def extract_details( self, details ):
		details = details.split( '\r\n' )
		try:
			return_details = dict()
			for value in details:
				val = value.split( ':' )
				if len( val ) == 2:
					return_details[ val[ 0 ].strip() ] = val[ 1 ].strip()
			return return_details;
		except:
			return False

	def error_handler( self, response ):
		errors = { 0 : 'Phone failure', 1 : 'No connection to phone', 2 : 'Phone adapter link reserved', 3 : 'Operation not allowed', 4 : 'Operation not supported', 5 : 'PH_SIM PIN required', 6 : 'PH_FSIM PIN required', 7 : 'PH_FSIM PUK required', 10 : 'SIM not inserted', 11 : 'SIM PIN required', 12 : 'SIM PUK required', 13 : 'SIM failure', 14 : 'SIM busy', 15 : 'SIM wrong', 16 : 'Incorrect password', 17 : 'SIM PIN2 required', 18 : 'SIM PUK2 required', 20 : 'Memory full', 21 : 'Invalid index', 22 : 'Not found', 23 : 'Memory failure', 24 : 'Text string too long', 25 : 'Invalid characters in text string', 26 : 'Dial string too long', 27 : 'Invalid characters in dial string', 30 : 'No network service', 31 : 'Network timeout', 32 : 'Network not allowed, emergency calls only', 40 : 'Network personalization PIN required', 41 : 'Network personalization PUK required', 42 : 'Network subset personalization PIN required', 43 : 'Network subset personalization PUK required', 44 : 'Service provider personalization PIN required', 45 : 'Service provider personalization PUK required', 46 : 'Corporate personalization PIN required', 47 : 'Corporate personalization PUK required', 48 : 'PH-SIM PUK required', 100 : 'Unknown error', 103 : 'Illegal MS', 106 : 'Illegal ME', 107 : 'GPRS services not allowed', 111 : 'PLMN not allowed', 112 : 'Location area not allowed', 113 : 'Roaming not allowed in this location area', 126 : 'Operation temporary not allowed', 132 : 'Service operation not supported', 133 : 'Requested service option not subscribed', 134 : 'Service option temporary out of order', 148 : 'Unspecified GPRS error', 149 : 'PDP authentication failure', 150 : 'Invalid mobile class', 256 : 'Operation temporarily not allowed', 257 : 'Call barred', 258 : 'Phone is busy', 259 : 'User abort', 260 : 'Invalid dial string', 261 : 'SS not executed', 262 : 'SIM Blocked', 263 : 'Invalid block', 772 : 'SIM powered down' }

		response = self.extract_details( response )
		if '+CME ERROR' in response and int( response[ '+CME ERROR' ] ) in errors:
			error = errors[ int( response[ '+CME ERROR' ] ) ]
		else:
			error = 'Unknown Error'
		self.errLabel.setStyleSheet( 'color: red;' )
		self.errLabel.setText( error )

	def success_msg( self, info ):
		self.errLabel.setStyleSheet( 'color: green;' )
		self.errLabel.setText( info )

	def change_mode( self ):
		command = self.network_commands[ self.mode.currentIndex() ]
		if command:
			command = self.send_command( 'AT^SYSCFG=' + str( command ) ).strip()
			if command != 'OK':
				self.error_handler( command )
			else:
				self.success_msg( 'Settings successfully set' )
				self.check()

	def send_command( self, command ):
		if not self.Serial:
			raise ValueError( 'Serial provided None' )
		else:
			self.Serial.write( ( str( command ) + '\r\n' ).encode( 'utf-8' ) )
			time.sleep( 1 )
			out = ''
			while self.Serial.in_waiting > 0:
				out += self.Serial.read( 1 ).decode( 'utf-8' )
			return out if out else ''

app = QtWidgets.QApplication( sys.argv )
dialog = QtWidgets.QDialog()
s = Main( dialog )
dialog.show()
app.exec_()