#define A do {} while(0)
#define B A A A A A A A A A A
#define C B B B B B B B B B B
#define D C C C C C C C C C C
#define E D D D D D D D D D D
#define F E E E E E E E E E E
#define G F F F F F F F F F F

int main() {
    G
}

