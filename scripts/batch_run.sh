function usage() {
    echo "Usage: $0 -p <profiles> -c"
    echo "  -p <profiles> : specify the profiles file"
    echo "  -c            : run chat only"
}

profiles=""
chat_only=0
while getopts "p:c" opt; do
    case ${opt} in
        p )
            profiles=$OPTARG
            ;;
        c )
            chat_only=1
            ;;
        \? )
            usage
            ;;
    esac
done

if [ -z "$profiles" ]; then
    usage
    exit 1
fi


echo "=================== Overview ====================="
if [ $chat_only -eq 1 ]; then
    exe=scripts/run_wrapper_co.sh
    echo -e "\033[33mRunning chat only\033[0m"
else
    exe=scripts/run_wrapper.sh
    echo -e "\033[33mRunning with tools\033[0m"
fi

profiles=$(cat $profiles)
echo "Profiles to run:"
total=0
for profile in $profiles; do
    echo "    $profile"
    total=$((total+1))
done
echo -e "\033[34mTotal profiles: $total\033[0m"


echo "==================== Running ====================="
result_file="vd.log"
index=0
passed=0
failed=0
unknown=0
for profile in $profiles; do
    index=$((index+1))
    printf "[%2s/%2s] %-10s ... " $index $total $profile

    # avoid too much output in the console
    start=`date +%s`
    bash $exe $profile > batch.out 2>&1
    end=`date +%s`
    printf "[%7.2fs] ..." $(echo "$end - $start" | bc -l)
    
    result=$(cat $result_file 2> /dev/null)
    if [ "$result" == "valid" ]; then
        echo -e "\033[32m[✓]\033[0m"
        passed=$((passed+1))
    elif [ "$result" == "invalid" ]; then
        echo -e "\033[31m[✗]\033[0m"
        failed=$((failed+1))
    else
        echo -e "\033[33m[?]\033[0m"
        unknown=$((unknown+1))
    fi

done

echo "==================== Summary ====================="
passed_percent=$(echo "scale=2; $passed * 100 / $total" | bc)
echo -e "\033[32m Passed: $passed ($passed_percent%)\033[0m"
echo -e "\033[31m Failed: $failed\033[0m"
echo -e "\033[33mUnknown: $unknown\033[0m"
echo -e "\033[34m  Total: $total\033[0m"
