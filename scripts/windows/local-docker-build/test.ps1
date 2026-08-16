$nasUsername = 'richard'
$nasPassword = 'EhZ.y2K3uWq!du&"W:D1P*Tn'

docker volume rm diaries-nas-test 2>$null

$nasUsername = 'diaries-docker'
$nasPassword = 'A7m4K9p2R6x8'

$opts = "addr=192.168.5.252,username=$nasUsername,password=$nasPassword,vers=3.0,ro"

$args = @(
    'volume', 'create',
    'diaries-nas-test',
    '--driver', 'local',
    '--opt', 'type=cifs',
    '--opt', 'device=//192.168.5.252/photo',
    '--opt', "o=$opts"
)

& docker @args

docker volume inspect diaries-nas-test

docker run --rm `
    -v diaries-nas-test:/test:ro `
    alpine ls -al /test
