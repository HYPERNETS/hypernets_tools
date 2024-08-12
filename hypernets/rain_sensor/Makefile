
CFLAGS = -Wall -O # Force expansion of inline functions

SRC = rain_sensor.c

NAME = rain_sensor

CC = gcc

all: clean bin

bin:
	$(CC) -o $(NAME) $(SRC) $(CFLAGS)
	sudo chown root $(NAME);  # Root has to own this
	sudo chmod 4555 $(NAME);  # Anybody can execute, setuid root for low level gpio access

clean:
	rm -f $(NAME)
