
// system, exit
#include <stdlib.h>

// read, write, fork, exec
#include <unistd.h>
#include <stdio.h>

#include "libmill.h"

#define true 1

void read_char( chan out ){

  yield();

  while(true){

    char in_buffer[ 4096 ];
    ssize_t in_len = read(0, in_buffer, sizeof(in_buffer));

    fprintf(stderr, "some stuff: %c\n", in_buffer[0]);

    if( in_len <= 0 ){
      break;
    }

    for(ssize_t offset = 0; offset < in_len ; offset ++ ){
      int send = in_buffer[offset];
      chs(out, int, send);
    }
  }

  chdone(out, int, (int)-1);

  chclose(out);
}

void process_input( chan in, chan out, chan out_var, char * open_pattern, char * close_pattern ){

  size_t escape_index = 0;

  enum state { Empty, Var } current_state = Empty;

  while( true ){

    int input = chr(in, int);

    if( input == -1 ){
      break;
    }

    if( current_state == Empty && input == open_pattern[escape_index] ){

      escape_index ++;

      if( open_pattern[ escape_index ] == 0 ){
        chs(out, int, -2);
        current_state = Var;
        escape_index = 0;
      }

    } else if ( current_state == Var && input == close_pattern[escape_index] ){

      escape_index ++;

      if( close_pattern[ escape_index ] == 0 ){
        chs(out_var, int, -2);
        current_state = Empty;
        escape_index = 0;
      }

    } else {

      // figure out where to send by state.
      chan * send_to = &out;
      if( current_state == Var ){
        send_to = &out_var;
      }

      if( escape_index > 0 ){

        char * buffer = open_pattern;
        if( current_state == Var ){
          buffer = close_pattern;
        }

        for(size_t i=0; i < escape_index; i++){
          int sending = buffer[i];
          chs(*send_to, int, sending);
        }

        escape_index = 0;
      }

      chs(*send_to, int, input);
    }

  }// end while

  chdone(out, int, -1);
  chdone(out_var, int, -1);

  chclose(out);
  chclose(out_var);

  chclose(in);
}

// has informal protocol:
// * -1 -> done, no more from me.
// * -2 -> unit done, flush output.
void write_output( chan from_fsm, chan from_var, chan signal_exit ){

  size_t offset = 0;
  char buffer[8192];

  int exit = 0;

  while(!exit){

    int sent = 0;

    choose {
      in(from_fsm, int, in_val):
        sent = in_val;
      in(from_var, int, in_val):
        sent = in_val;
      end
    }

    if( sent == -1 ){
      exit = 1;
    }

    if( sent != -1 && sent != -2 ){
      buffer[offset] = (char)sent;
      offset++;
    }

    if( sent == -2 || offset >= sizeof(buffer) -1 ){

      ssize_t written = 0;
      while(written < offset){
        ssize_t retval = write(1, buffer + written, offset - written);

        if( retval < 0 ){
          exit = 1;
        } else {
          written += retval;
        }
      }// end write loop

      offset = 0;
    }


  } //end while(!exit)

  if(offset > 0 ){
    int r = write(1, buffer, offset);
  }

  chclose(from_fsm);
  chclose(from_var);

  chs(signal_exit, int, 1);
  chclose(signal_exit);
}

void variable_lookup( chan from_fsm, chan to_output ){

  size_t offset = 0;
  char buffer[8192];

  int running = 1;

  while(running){

    int sent = chr(from_fsm, int);

    if( sent == -1 ){

      running = 0;

    } else if( sent != -2 ){

      buffer[offset] = (char)sent;
      offset++;

      if( offset >= sizeof(buffer) -1 ){
        buffer[ sizeof(buffer) - 1 ] = 0;
        fprintf(stderr, "variable is too large: %s", buffer );
        exit(-2);
      }

    } else { // sent == -2
     
      // long case...
      buffer[offset] = 0;

      int ret = system(buffer);

      if( ret != 0 ){
        fprintf(stderr, "error during execution: '%s'", buffer );
        exit(-2);
      }

      offset = 0; 
    }

  }

  chclose(from_fsm);
  chdone(to_output, int, -1);
  chclose(to_output);

}


int main(){

  chan in_fsm = chmake(int, 0);
  go( read_char( chdup(in_fsm) ) );

  chan fsm_out = chmake(int, 0);
  chan fsm_var = chmake(int, 0);

  go( process_input( chdup(in_fsm), chdup(fsm_out), chdup(fsm_var), "{{", "}}") );
  chclose(in_fsm);

  chan var_out = chmake(int, 0);
  go( variable_lookup( chdup(fsm_var), chdup(var_out) ) );
  chclose(fsm_var);

  chan signal_exit = chmake(int, 0);

  go( write_output( chdup(fsm_out), chdup(var_out), chdup(signal_exit) ) );
  chclose(fsm_out);
  chclose(var_out);

  yield();

  int exit = chr(signal_exit, int);
  chclose(signal_exit);
}
