#!/bin/bash
set -e

# If ELASTICSEARCH_HOST is set, patch corpus.json to point to it
if [ -n "$ELASTICSEARCH_HOST" ]; then
    CONF_FILE="/app/conf/corpus.json"
    if [ -f "$CONF_FILE" ]; then
        ES_URL="http://${ELASTICSEARCH_HOST}:9200"
        # Use python to safely patch JSON
        python3 -c "
import json, sys
with open('$CONF_FILE', 'r', encoding='utf-8') as f:
    conf = json.load(f)
conf['elastic_url'] = '$ES_URL'
with open('$CONF_FILE', 'w', encoding='utf-8') as f:
    json.dump(conf, f, ensure_ascii=False, indent=2)
print(f'Patched elastic_url -> $ES_URL')
"
    fi
fi

exec "$@"
