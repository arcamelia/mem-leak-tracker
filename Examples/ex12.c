int copyStrings(char *str1, char *str2, char *str3) {
    char *a, *b, *c, *toPrint;
    *a = "temp a";
    *b = "temp b";
    *c = "temp c";

    if (str1) {
        a = malloc(100 * sizeof(char));
        a = strcpy(a, str1);
    }

    if (str2) {
        b = malloc(100 * sizeof(char));
        b = strcpy(a, str2);
    }

    if (str3) {
        c = malloc(100 * sizeof(char));
        c = strcpy(a, str3);
        free(c);
    }

    toPrint = a;
    printf("toPrint: %s\n", toPrint);

    return 0;
}