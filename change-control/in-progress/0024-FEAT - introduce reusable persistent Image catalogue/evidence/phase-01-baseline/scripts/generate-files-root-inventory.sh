

input="/cygdrive/p/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files"
output="../files-root-inventory.txt"

tree -a -f -s -D -o "${output}" "${input}"
