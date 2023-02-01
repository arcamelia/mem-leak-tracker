int main() {
    while (1) {
        int * c = malloc(4);
    }

    int * d;
    while(1) {
        d = malloc(4);
    }

    int * e = malloc(4);
    while(1) {
        free(e);
    }
}