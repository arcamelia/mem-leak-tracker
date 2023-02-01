int reallocate() {
    int *a = malloc(sizeof(int));
    int *b;

    int i = 0;
    while (i < 6) {
        b = a;
        a = malloc(sizeof(int));
    }

}