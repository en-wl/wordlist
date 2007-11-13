
#include <iostream>
#include <string>
#include "deaccent.hh"

using namespace std;

int main() {
  int c;
  string line;
  while ( getline(cin, line) ) 
    {
      for (unsigned int i = 0; i != line.size(); ++i) {
	if (line[i] != deaccent(line[i])) {
	  cout << line << '\n';
	  break;
	}
      }
    }
}
