function usage() {
    echo "Usage: $0 -p <profiles> [-n]"
    echo "  -p <profiles> : specify the profiles file"
    echo "  -n            : disable constraint"
    exit 1
}

exe=scripts/run_chat.sh
if [ ! -f $exe ]; then
    echo "Error: $exe does not exist"
    exit 1
fi

PROFILES=""
NO_CONSTRAINT=0
while getopts "p:nh" opt; do
    case ${opt} in
        p )
            PROFILES=$OPTARG
            ;;
        n )
            NO_CONSTRAINT=1
            ;;
        h )
            usage
            ;;
    esac
done

if [ -z "$PROFILES" ]; then
    usage
fi
if [ ! -f "$PROFILES" ]; then
    echo "Error: $PROFILES does not exist"
    exit 1
fi

echo "================ Overview ==============="
echo -e "\033[35mBatch Repair with Chat-Only\033[0m"
options="-k"
if [ $NO_CONSTRAINT -eq 1 ]; then
    options="$options -n"
    echo -e "\033[33mConstraint disabled\033[0m"
fi

PROFILES=$(cat $PROFILES)
echo "Profiles to run:"
total=0
for profile in $PROFILES; do
    echo "    $profile"
    total=$((total+1))
done
if [ $total -eq 0 ]; then
    echo "No profile to run"
    exit 0
fi
echo -e "\033[34mTotal profiles: $total\033[0m"

echo "========================== Running =========================="
result_file="validate.lock"
index=0
passed=0
failed=0
exception=0
all_start=`date +%s`
for profile in $PROFILES; do
    index=$((index+1))
    printf "[%2s/%2s] %-30s ... " $index $total $profile

    # avoid too much output in the console
    start=`date +%s`
    bash $exe -p $profile $options > batch.out 2>&1
    end=`date +%s`
    printf "[%7.2fs] ... " $(echo "$end - $start" | bc -l)
    
    result=$(cat $result_file 2> /dev/null)
    if [ "$result" == "valid" ]; then
        echo -e "\033[32m[✓]\033[0m"
        passed=$((passed + 1))
    elif [ "$result" == "invalid" ]; then
        echo -e "\033[31m[✗]\033[0m"
        failed=$((failed + 1))
    else
        echo -e "\033[33m[?]\033[0m"
        exception=$((exception + 1))
    fi
done
all_end=`date +%s`

echo "========================= Summary ==========================="
passed_percent=$(echo "scale=2; $passed * 100 / $total" | bc)
echo -e "\033[32m     Passed: $passed ($passed_percent%)\033[0m"
echo -e "\033[31m     Failed: $failed\033[0m"
echo -e "\033[33mOther Error: $exception\033[0m"
echo -e "\033[34m      Total: $total\033[0m"

printf "Total time: [%10.2fs]" $(echo "$all_end - $all_start" | bc -l)
echo ""
