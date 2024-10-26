function usage() {
    echo "Usage: $0 <profiles>"
    echo "  <profiles> : specify the profiles file"
}

profiles=${1:?$(usage)}

echo "Batch run with tools"
./scripts/batch_run.sh -p $profiles

echo ""

echo "Batch run chat only"
./scripts/batch_run.sh -p $profiles -c

