# 0031 Step 16 final effective path map

| Mode | Isolated committed database | Isolated committed Files | Test common database | Test common Files |
| --- | --- | --- | --- | --- |
| development-infrastructure | ./data/database/development-infrastructure | files-development-infrastructure | ./data/database/common | files-development-common |
| local-docker-build | ./data/database/local-docker-build | files-local-docker-build | ./data/database/common | files-development-common |
| local-published-smoke | ./data/database/local-published-smoke | files-local-published-smoke | ./data/database/common | files-development-common |

The common rows above are a temporary Step 16 precedence fixture. They do not modify the developer-owned ignored `config/environments/local.env`.
