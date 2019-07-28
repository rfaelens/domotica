# About this document
The Danabridge is a mobile app that was published by Danalock in 07-APR-2016 (last updated in 2018).
It allows the use of IFTTT for a Bluetooth-only Danalock.

This file documents how the Danabridge works, in the hopes of understanding the Bluetooth danalock protocol and providing an open-source implementation. I do not like being forced to buy a Danabridge V3 hardware, when this can also be done by a Raspberry Pi.

# Configuration of the app
The app logs in to a mobile API provided by Danalock. The API is used to request the danalocks registered to the account, checking if this lock is within bluetooth range, and registering the smartphone as a bridge.

```{bash}
URL=https://ekey-bridge.poly-control.com/mobileapi/v1
JSON='{"username": "'$1'", "password":"'$2'", "local_identifier":"'test'"}'

echo "Logging in"
RESULT=$(curl -H "Content-Type: application/json" --data "${JSON}" ${URL}/device/get_access_token)
echo $RESULT

echo "Response: $RESULT"
TOKEN=$(echo $RESULT | jq -r '.access_token')
echo "Access token: $TOKEN"
```

Several API endpoints are described in `danalock.polycontrol.dk.danalock_bridge_app.bridge.Bridge`.

# Sending requests to the smartphone
Requests are sent to the smartphone via Google's Google Cloud Messaging (GCM) service. Unfortunately, this service was discontinued (see https://developers.google.com/cloud-messaging/android/android-migrate-gcmlistener), and this is probably why the app was discontinued in favor of the hardware "Danabridge V3".

The class is a good starting point for the actions that can be performed with the lock. `danalock.polycontrol.dk.danalock_bridge_app.gcm.GcmMessageService`

- connectAndPerformAction

# Unlocking
The unlocking and communication protocol itself was patented by Poly-Care APS (Danalock company), see http://www.sumobrain.com/patents/wipo/Method-operating-door-lock-by/WO2016023558A1.pdf.

The communication between the lock and the phone is encrypted using a variety of possible keys. In the most locked-down scenario, the Danalock server submits a SLEK-encrypted Phone Lock Communication Initiation Record. The SLEK is a session key that was encrypted by Danalock and which can only be decrypted by the lock; the mobile phone is just a messenger. The PLCIR contains a new session key (which the phone *does* know), a time period for validity, and optionally permission data.

The danabridge therefore communicates with the lock as follows:

1. Receives a GCM message (`GcmMessageService#onMessageReceived(String from, Bundle data)`). Decodes the message and get request_id, mac, action, plek, plcir.
2. Generate the DLKey
```
String paramString1 = macAddress;
String paramString2 = plcir;
String paramString3 = plek;
return DLKey.getInstance(
  String.format(
     "{\"user\":{\"user_id\":\"101337\",\"token_id\":\"0\",\"can_remote\":1,\"can_share\":0,\"can_delete\":0,\"external\":{\"id\":\"0\",\"source\":\"0\"}},\"name\":\"remote V3\",\"product\":{\"firmware\":{\"firmware_version\":\"0.7.6\",\"variation\":\"DANALOCKV3-BT\",\"pcb_version\":\"101-025_D1\",\"updates\":false},\"name\":\"danalockv3\",\"type\":\"danalock\"},\"valid_from\":1511862028,\"valid_to\":2147472000,\"time_restrictions\":[],\"permissions\":[{\"id\":\"1\",\"description\":\"\"},{\"id\":\"2\",\"description\":\"\"},{\"id\":\"3\",\"description\":\"\"},{\"id\":\"4\",\"description\":\"\"},{\"id\":\"5\",\"description\":\"\"},{\"id\":\"6\",\"description\":\"\"},{\"id\":\"7\",\"description\":\"\"},{\"id\":\"8\",\"description\":\"\"},{\"id\":\"9\",\"description\":\"\"},{\"id\":\"10\",\"description\":\"\"}],\"serial_number\":\"%s\",\"login_token\":\"%s\",\"advertising_key\":\"8bdLPF6mlxnr+i40zBtgRA==\",\"data\":[]}", 
	new Object[] { paramString1, paramString2 }), 
  paramString1, "remote V3", DLKey.DLKeyType.V3);
```

This simply creates a `DLV3Key` which is a data structure to describe the lock.
3. Create a DLDevice using `DLDevice.getDevice()`, which creates a `DanalockV3` object. A DanalockV3 is considered a DMILock.
4. Scan for the device, and finally connect and perform the action using
`DeviceConnector.getInstance().connectToDevice(paramDanaDevice, new GcmMessageService.3(this, action, paramDanaDevice, request_id));`
5. Finally, the onConnected method of the callback fires (see `GcmMessageService$3#onConnected()`), which locks or unlocks the lock.
6. From the `DanalockV3` interface, we go to `DMILock`, which (via numerous callbacks) finally executes `Dmi_AfiClient_Lock.unlock()`
7. This finally ends up in the Dmi class, specifically the native method `Dmi_AfiClient_LockOperate`. This static class implements the communication protocol (it gets transferred every byte sent and received, see Dmi.dataReceived()).
3. Starts scanning for the BLE device, using `startScanningForDevice()`
1. Receives PLCIR and PLEK from Danalock via GCM.
2. Forwards PLCIR to the lock. Uses the

