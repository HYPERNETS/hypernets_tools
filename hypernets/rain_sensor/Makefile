
CFLAGS = -Wall -O # Force expansion of inline functions
PFLAGS = -fPIC -shared

SRC = rain_sensor_module.c

NAME = rain_sensor
MODULE_NAME = $(NAME)_module.so

CC = gcc

all: clean module bin

bin:
	$(CC) -o $(NAME) $(SRC) $(CFLAGS)
	sudo chown root $(NAME);  # Root has to own this
	sudo chmod 4555 $(NAME);  # Anybody can execute

module:
	$(CC) -o $(MODULE_NAME) $(SRC) $(CFLAGS) $(PFLAGS)

clean:
	rm -f $(MODULE_NAME) $(NAME)
