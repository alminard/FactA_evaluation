#!/bin/sh

CURRENTPATH=$(pwd)

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink

  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located 
 
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

cd $DIR


function usage(){
    printf "Usage:\n"
    printf "\t-h           : print this message\n"
    printf "\t-g           : path to the folder containing gold files\n"
    printf "\t-s           : path to the folder containing system files\n"
    printf "\t-t           : path to a folder in which temporary files will be saved\n"
    printf "\t-r           : patht to the file in which the results will be printed\n"
}



OPTS=$( getopt -o h,g,s,r,t -- "$@" )
if [ $? != 0 ]
then
    exit 1
fi

GOLD=''
SYS=''
RES=''
TEMP=''

while true ; do
    #echo $1
    case "$1" in
	-h) usage;
	    exit 0;;
	-g) GOLD=$2;
	    shift 2;;
	-s) SYS=$2;
	    shift 2;;
	-r) RES=$2;
	    shift 2;;
	-t) TEMP=$2;
	    shift 2;;
	--) shift; break;;
	*) break;;
    esac
done



if [[ "$GOLD" != /* ]]; then
    GOLD="$CURRENTPATH"/"$GOLD"
fi
if [[ "$SYS" != /* ]]; then
    SYS="$CURRENTPATH"/"$SYS"
fi
if [[ "$RES" != /* ]] && [[ "$RES" != '' ]]; then
    RES="$CURRENTPATH"/"$RES"
fi
if [[ "$TEMP" != /* ]]; then
    TEMP="$CURRENTPATH"/"$TEMP"
fi

if [[ ! -d "$TEMP" ]]; then
    mkdir "$TEMP"
fi

if [[ ! -d "$TEMP"/gold_CoNLL/ ]]; then
    mkdir "$TEMP"/gold_CoNLL/
fi
if [[ ! -d "$TEMP"/sys_CoNLL/ ]]; then
    mkdir "$TEMP"/sys_CoNLL/
fi


python cat_to_conll_converter.py "$GOLD" "$TEMP"/gold_CoNLL/ rules_FV.txt

python cat_to_conll_converter.py "$SYS" "$TEMP"/sys_CoNLL/ rules_FV.txt

if [[ $RES == '' ]]; then
    perl scorer_factuality.pl $TEMP/gold_CoNLL/ $TEMP/sys_CoNLL/ 
else
    perl scorer_factuality.pl $TEMP/gold_CoNLL/ $TEMP/sys_CoNLL/ >$RES
fi

exit 0
