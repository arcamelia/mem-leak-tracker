void func(int* r) {
    r = malloc (4);
}

int main()  
{
    int* c;
    func(c);
    return 0;
}