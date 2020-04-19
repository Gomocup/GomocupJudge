#include "pisqpipe.h"
#include <windows.h>
#include <stdlib.h>

const char *infotext="name=\"Random\", author=\"Petr Lastovicka\", version=\"3.2\", country=\"Czech Republic\", www=\"http://petr.lastovicka.sweb.cz\"";

#define MAX_BOARD 100
int board[MAX_BOARD][MAX_BOARD];
static unsigned seed;


void brain_init() 
{
  if(width<5 || height<5){
    pipeOut("ERROR size of the board");
    return;
  }
  if(width>MAX_BOARD || height>MAX_BOARD){
    pipeOut("ERROR Maximal board size is %d", MAX_BOARD);
    return;
  }
  seed=start_time;
  pipeOut("OK");
}

void brain_restart_helper()
{
	int x, y;
	for (x = 0; x < width; x++) {
		for (y = 0; y < height; y++) {
			board[x][y] = 0;
		}
	}
}

void brain_restart()
{
	brain_restart_helper();
	pipeOut("OK");
}

int isFree(int x, int y)
{
  return x>=0 && y>=0 && x<width && y<height && board[x][y]==0;
}

void brain_my(int x,int y)
{
  if(isFree(x,y)){
    board[x][y]=1;
  }else{
    pipeOut("ERROR my move [%d,%d]",x,y);
  }
}

void brain_opponents(int x,int y) 
{
  if(isFree(x,y)){
    board[x][y]=2;
  }else{
    pipeOut("ERROR opponents's move [%d,%d]",x,y);
  }
}

void brain_block(int x,int y)
{
  if(isFree(x,y)){
    board[x][y]=3;
  }else{
    pipeOut("ERROR winning move [%d,%d]",x,y);
  }
}

int brain_takeback(int x,int y)
{
  if(x>=0 && y>=0 && x<width && y<height && board[x][y]!=0){
    board[x][y]=0;
    return 0;
  }
  return 2;
}

unsigned rnd(unsigned n)
{
  seed=seed*367413989+174680251;
  return (unsigned)(UInt32x32To64(n,seed)>>32);
}

void brain_turn() 
{
  int x,y,i;

  i=-1;
  do{
    x=rnd(width);
    y=rnd(height);
    i++;
    if(terminateAI) return;
  }while(!isFree(x,y));

  if(i>1) pipeOut("DEBUG %d coordinates didn't hit an empty field",i);
  do_mymove(x,y);
}

void brain_turn_swap2()
{
	if (stage == 1)
	{
		pipeOut("7,7 8,7 9,9");
	}
	else if (stage == 2)
	{
		int option = rand() % 3;
		if (option == 0)
			pipeOut("SWAP");
		else if (option == 1)
			brain_turn();
		else
		{
			int x1, y1, x2, y2, i;
			i = -1;
			do {
				x1 = rnd(width);
				y1 = rnd(height);
				i++;
				if (terminateAI) return;
			} while (!isFree(x1, y1));
			brain_my(x1, y1);
			i = -1;
			do {
				x2 = rnd(width);
				y2 = rnd(height);
				i++;
				if (terminateAI) return;
			} while (!isFree(x2, y2));
			brain_my(x2, y2);
			pipeOut("%d,%d %d,%d", x1, y1, x2, y2);
		}
	}
	else
	{
		int option = rand() % 2;
		if (option == 0)
			pipeOut("SWAP");
		else
			brain_turn();
	}
	brain_restart_helper();
}

void brain_end()
{
}

#ifdef DEBUG_EVAL
#include <windows.h>

void brain_eval(int x,int y)
{
  HDC dc;
  HWND wnd;
  RECT rc;
  char c;
  wnd=GetForegroundWindow();
  dc= GetDC(wnd);
  GetClientRect(wnd,&rc);
  c=(char)(board[x][y]+'0');
  TextOut(dc, rc.right-15, 3, &c, 1);
  ReleaseDC(wnd,dc);
}

#endif
