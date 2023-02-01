int main() {
    int* a = malloc(4);
    int* b = malloc(4);
    b = a;
    free(b);
}