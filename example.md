cd /
cd opt/
cd research-backend/


curl -s -X POST http://157.245.99.84/analyze/both \
  -F "file=@H:/short16k.wav" \
  -F "ref_text=He was happy"
  -F "user_id=test123" | jq

curl -X POST http://157.245.99.84/analyze/both \
    -F "file=@H:/short16k.wav" \
    -F "user_id=test123"

curl -X POST http://157.245.99.84/analytics/test123/recompute

curl -X GET http://157.245.99.84/analytics/test123

curl -X GET http://157.245.99.84/analytics/test123?force=true

curl -x GET http://157.245.99.84/wakness/test123

curl -x GET http://157.245.99.84/wakness/summary/test123?limit=50