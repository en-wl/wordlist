
#include <iostream>
#include <fstream>
#include <map>
#include <string>

typedef unsigned char uchar;

int main() {
  string temp;
  string word;
  
  char t0[255];

  char strip[256];

  ifstream in0("cp437.dat");
  getline(in0, temp);
  getline(in0, temp);
  int i = 0;
  int j, j0, j1, j2, j3, j4, j5;
  while (!in0.eof()) {
    in0 >> j0 >> t0 >> j1 >> j2 >> j3 >> j4; // all ignored
    in0 >> j;
    strip[i] = (char)j;
    in0 >> j5; //also ignored
    ++i;
  }

  map<string,string> pos;

  in0.close();

  ifstream in1("/home/kevina/moby/mpos/mobyposi.i");
  while (!in1.eof()) {
    getline(in1, temp, '\r');
    if (temp.size() == 0) break;
    word = "";
    unsigned int i;
    for (i = 0; i != temp.size(); ++i) {
      char c = (uchar)temp[i] < 0x80 ? temp[i] : strip[(uchar)temp[i]];
      if (c == '\x91')
	word += "ae";
      else if (c == '\x9C' || c == '\x9D' || c == '\x9E')
	word += '$';
      else if (c == '\xBE')
	word += '~';
      else if (c == '\xD7') 
	break;
      else
	word += c;
    }
    ++i;
    string & t = pos[word];
    for (; i < temp.size(); ++i) {
      if (t.find(temp[i]) == string::npos)
	t += temp[i];
    }
  }
  in1.close();

  in0.close();
  in0.open("/aux/local/wordnet1.6/dict/noun.lst");
  while(getline(in0, word)) {
    string & t = pos[word];
    if (t.size() == 0) t += '|';
    char c = word.find_first_of(" ") == string::npos ? 'N' : 'h';
    if (t.find(c) == string::npos)
      t += c;
  }
  in0.close();
  in0.open("/aux/local/wordnet1.6/dict/verb.lst");
  while(getline(in0, word)) {
    string & t = pos[word];
    if (t.size() == 0) t += '|';
    if (t.find('V') == string::npos)
      t += 'V';
  }
  in0.close();
  in0.open("/aux/local/wordnet1.6/dict/adj.lst");
  while(getline(in0, word)) {
    string & t = pos[word];
    if (t.size() == 0) t += '|';
    if (t.find('A') == string::npos)
      t += 'A';
  }
  in0.close();
  in0.open("/aux/local/wordnet1.6/dict/adv.lst");
  while(getline(in0, word)) {
    string & t = pos[word];
    if (t.size() == 0) t += '|';
    if (t.find('v') == string::npos)
      t += 'v';
  }
  
  map<string, string>::iterator p, end;
  p   = pos.begin();
  end = pos.end();
  while (p != end) {
    cout << p->first << '\t' << p->second << endl;
    ++p;
  }
}






