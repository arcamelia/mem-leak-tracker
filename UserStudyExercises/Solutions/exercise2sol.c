int main() {

   char name[100];
   char *description;

   strcpy(name, "Zara Ali");

   /* allocate memory dynamically */
   description = malloc( 200 * sizeof(char) );
	
   if( description == NULL ) {
      fprintf(stderr, "Error - unable to allocate required memory\n");
   } else {
      strcpy(description, "Zara Ali a DPS student in class 10th");
      printf("Name = %s\n", name);
      printf("Description: %s\n", description); 
      free(description); 
      // Technically, there is no memory leak since the only way to get into the first block is if nothing was allocated. Our program gives a warning for this case.
   }
}