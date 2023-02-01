void swap(int *a, int *b) {
  int temp = *a;
  *a = *b;
  *b = temp;
} 

void bubbleSort(int array[], int n) {
  int i, j;
  for (i = 0; i < n-1; i++) {	
    for (j = 0; j < n-i-1; j++) {
      if (array[j] > array[j+1]) {
        int * a = malloc(sizeof(int));
        int * b = malloc(sizeof(int));
        *a = array[j];
        *b = array[j+1];
        swap(a, b);
        free(a);
        free(b);
      }
    }
  }
} 

void printArray(int array[], int size) {
  int i;
  for (i=0; i < size; i++) {
    printf("%d ", array[i]);
  }
} 

int main() {
  int array[] = {89, 32, 20, 113, -15};
  int size = sizeof(array)/sizeof(array[0]);
  bubbleSort(array, size);
  printf("Sorted array: ");
  printArray(array, size);
  return 0;
} // No memory leaks!