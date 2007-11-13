
#include <cstdio>

#include "deaccent.hh"

using namespace std;

int main() {
  int c;
  while ( c = getchar(), c != -1 ) 
  {
    putchar(deaccent(c));
  }
}
