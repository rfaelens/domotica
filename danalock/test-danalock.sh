#!/bin/sh
USER=$1
PASSWORD=$2

#Bridge#getAccessToken
#localHashMap.put("username", getUsername(paramActivity));
#localHashMap.put("password", getPassword(paramActivity));
#localHashMap.put("uri", "device/get_access_token");
#localHashMap.put("local_identifier", getDeviceId(paramActivity));
#localHashMap.put("method", "POST");

# HttpsClient: mobileapi/v1/
# Content-Type: application/json
URL=https://ekey-bridge.poly-control.com/mobileapi/v1
JSON='{"username": "'$1'", "password":"'$2'", "local_identifier":"'test'"}'

echo "Logging in"
RESULT=$(curl -H "Content-Type: application/json" --data "${JSON}" ${URL}/device/get_access_token)
echo $RESULT

echo "Response: $RESULT"
TOKEN=$(echo $RESULT | jq -r '.access_token')
echo "Access token: $TOKEN"


