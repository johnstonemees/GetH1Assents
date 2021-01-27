#! /bin/bash
#1.delete http/https and ,
python3 h1assents.py 0 &&
cat all_assents.txt | sed 's/http\(s\):\/\///g' | sed 's/http:\/\///g' |  sed 's/\/\*//g' | sed "s/,/\r/g" | sed 's/\/$//g' > modify.txt &&
#2.sort all the domain and create folders
#cat modify.txt | sed 's/*//g' | awk -F '.' '{print $(NF-1)}' | sort -u | while read line;do if [ ! -d $line ];then mkdir $line;fi;done
#3.send *.domain to oneforall
cat modify.txt | grep '*\.' | sed "s/\///g" | sed 's/\*\.//g' > prepareforenmusubdomains.txt &&
cat modify.txt | grep -v '*\.' > scopedomain.txt &&
subfinder -all -dL prepareforenmusubdomains.txt -o subdomain.txt &&
cat subdomain.txt scopedomain.txt > alldomains.txt &&
vulffuf -l alldomains.txt -t ~/nuclei-templates -o bbresult.txt
