/*
 * NewRemoteSwitch library v1.1.0 (20130601) made by Randy Simons http://randysimons.nl/
 *
 * License: GPLv3. See license.txt
 */

#ifndef NewRemoteTransmitter_h
#define NewRemoteTransmitter_h

//#include <Arduino.h>

/**
* NewRemoteTransmitter provides a generic class for simulation of common RF remote controls, like the A-series
* 'Klik aan Klik uit'-system (http://www.klikaanklikuit.nl/), used to remotely switch lights etc.
*
* This class is meant for new-style remotes, usually accompanied by receivers with "code learning"
* capabilities. For other remotes, use the RemoteTransmitter class.
*
* Hardware required for this library: a 433MHz/434MHz SAW oscillator transmitter, e.g.
* http://www.sparkfun.com/products/10534
* http://www.conrad.nl/goto/?product=130428
*
* Notes:
* - I measured the period length with an oscilloscope, using a A-series KAKU transmitter. Other devices
*   or manufacturers may use other period length. Use the ShowReceivedCodeNewRemote example to find the
*   period length for your devices.
* - You can copy the address of your "real" remotes, so you won't have to learn new codes into the receivers.
*   In effect this duplicates a remote. But you can also pick a random number in the range 0..2^26-1.
*/
class NewRemoteTransmitter {
	public:
		/**
		* Constructor.
		*
		* To obtain the correct period length, use the ShowReceivedCodeNewRemote example, or you
		* can use an oscilloscope.
		*
		* @param address	Address of this transmitter [0..2^26-1] Duplicate the address of your hardware, or choose a random number.
		* @param pin		Output pin on Arduino to which the transmitter is connected
		* @param periodusec	Duration of one period, in microseconds. One bit takes 8 periods (but only 4 for 'dim' signal).
		* @param repeats	[0..8] The 2log-Number of times the signal is repeated. The actual number of repeats will be 2^repeats. 2 would be bare minimum, 4 seems robust, 8 is maximum (and overkill).
		*/
		NewRemoteTransmitter(unsigned long address, unsigned long pin, unsigned int periodusec = 260, unsigned long repeats = 4);

		/**
		 * Send on/off command to the address group.
		 *
		 * @param switchOn  True to send "on" signal, false to send "off" signal.
		 */
		void sendGroup(unsigned long switchOn);

		/**
		 * Send on/off command to an unit on the current address.
		 *
		 * @param unit      [0..15] target unit.
		 * @param switchOn  True to send "on" signal, false to send "off" signal.
		 */
		void sendUnit(unsigned long unit, unsigned long switchOn);

		/**
		 * Send dim value to an unit on the current address.
		 *
		 * @param unit      [0..15] target unit.
		 * @param dimLevel  [0..15] Dim level. 0 for off, 15 for brightest level.
		 */
		void sendDim(unsigned long unit, unsigned long dimLevel);

		/**
		 * Resety the adresss of the KAKU
		 *
		 * @param address      [0..256] Kaku Adress.
		 */
		void setAddress(unsigned long address);


	protected:
		unsigned long _address;		// Address of this transmitter.
		unsigned long _pin;					// Transmitter output pin
		unsigned int _periodusec;	// Oscillator period in microseconds
		unsigned long _repeats;				// Number over repetitions of one telegram

		/**
		 * Transmits start-pulse
		 */
		void _sendStartPulse();

		/**
		 * Transmits address part
		 */
		void _sendAddress();

		/**
		 * Transmits unit part.
		 *
		 * @param unit      [0-15] target unit.
		 */
		void _sendUnit(unsigned long unit);

		/**
		 * Transmits stop pulse.
		 */
		void _sendStopPulse();

		/**
		 * Transmits a single bit.
		 *
		 * @param isBitOne	True, to send '1', false to send '0'.
		 */
		void _sendBit(unsigned long isBitOne);
};
#endif

