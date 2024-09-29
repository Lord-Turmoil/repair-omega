#include <stdio.h>
#include <assert.h>

/**
 * @brief Sum the elements of an array
 * @param arr The array to sum
 * @param count The number of elements in the array
 */
int sum(int *arr, int count)
{
    int total = 0;
    for (int i = 0; i <= count; i++)
    {
        total += arr[i];
    }
    assert(total == 6);

    return total;
}

int main(int argc, char *argv[])
{
    for (int i = 0; i < argc; i++)
    {
        printf("argv[%d]: %s\n", i, argv[i]);
    }

    int arr[3] = {1, 2, 3};
    int total = sum(arr, 3);

    printf("total: %d\n", total);

    return 0;
}