int main() {
    int* c = malloc(16);
    c = malloc(8);
    free(c);
}