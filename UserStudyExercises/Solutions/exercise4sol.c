int main(int argc, char *argv[]) {
    char *mem = malloc( sizeof(char) * 20);

    if (mem == NULL) {
        fprintf(stderr, "Unable to allocate enough memory for mem!\n");
        return -1;
    }
    
    strcopy(mem, argv[1]);
    printf("the word you entered: %s\n", *mem);
   
    mem = malloc( sizeof(char) * 30); // Memory allocated on line 5 was not freed.

    if (mem == NULL) {
        fprintf(stderr, "Unable to allocate enough memory for array!\n");
        return -1;
    }

    free(mem);

    return 0; 
}