MAJOR := 0
MINOR := 2
NAME := hypstar
VERSION := $(MAJOR).$(MINOR)

CC := g++
BUILD_DIR := build
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

C_SOURCES := $(wildcard src/*.cpp)
C_SOURCES += $(wildcard src/serial/*.cpp)
C_SOURCES += $(wildcard src/utils/*.cpp)
OBJECTS := $(addprefix $(BUILD_DIR)/,$(notdir $(C_SOURCES:.cpp=.o)))

vpath %.cpp src:src/serial/:src/utils/
vpath %.h inc/:inc/serial/:inc/utils/

INCLUDES = -Iinc \
	-Iinc/serial \
	-Iinc/utils

CFLAGS := -fPIC -O0 -g -Wall -Werror $(INCLUDES) -M

lib: $(BUILD_DIR)/lib$(NAME).so

test_%: $(BUILD_DIR)/lib$(NAME).so
	@echo --------------------------
	@echo Building $@
	@echo --------------------------
	$(CC) $(INCLUDES) -L./$(BUILD_DIR) -Wl,-rpath=./$(BUILD_DIR) -o $(BUILD_DIR)/$@ test/$@.c -lhypstar

	@echo --------------------------
	@echo Executing $@
	@echo --------------------------
	./$(BUILD_DIR)/$@
	

$(BUILD_DIR)/lib$(NAME).so: $(BUILD_DIR)/lib$(NAME).so.$(VERSION)
	@echo ----- INFO: Linking lib 
	ln -s lib$(NAME).so.$(VERSION) $(BUILD_DIR)/lib$(NAME).so

$(BUILD_DIR)/lib$(NAME).so.$(VERSION): $(OBJECTS) 
	@echo ----- INFO: Building lib
	@echo C_SOURCES = $(C_SOURCES)
	@echo OBJECTS = $(OBJECTS)
	$(CC) -fPIC -shared -Wl,--export-dynamic -o $@ $(OBJECTS)

$(BUILD_DIR)/%.o : %.cpp | $(BUILD_DIR)
	@echo ----- INFO: Building file $<
	$(CC) -fPIC -O0 -g -Wall -Werror $(INCLUDES) -c $< -o $@

.PHONY: clean
clean:
	$(RM) -r $(BUILD_DIR)
install: lib
	$(RM) /usr/lib/lib$(NAME).so
	cp $(BUILD_DIR)/lib$(NAME).so.$(VERSION) /usr/lib/
	ln -s lib$(NAME).so.$(VERSION) /usr/lib/lib$(NAME).so