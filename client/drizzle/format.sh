#!/bin/bash

# 더 안전하게 mode만 교체
sed -i '' "s/mode: 'string'/mode: 'date'/g" ./drizzle/schema.ts

# 코드 정리 (선택사항)
# npx eslint --fix ./drizzle/schema.ts
# npx eslint --fix ./drizzle/relations.ts
