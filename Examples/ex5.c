int foo() {
    int* c = malloc(4);
    return c;
}

int main() {
    int* a = foo();
    return 0;
}