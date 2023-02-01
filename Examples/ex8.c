int main(int argc, char *argv[]) {
    int x = argv[1];
    int* mem = malloc(4);
    if (x > 0) {
        free(mem);
    }
    return 0;
}