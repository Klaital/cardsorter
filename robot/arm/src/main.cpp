#include "ESPMax.h"
#include "_espmax.h"
#include "SuctionNozzle.h"
#include "Buzzer.h"
#include <Arduino.h>
#include <Position.h>

// Various action scripts

// Rotate the head
void rotate_home();
void rotate(int dst);

// positions for the various card stacks
float pos_source[3] = { 0, -(L1 + L3 + L4)+5, (L0 + L2)-1 };
Position source(0, -(L1 + L3 + L4)+10, 6.0); // input stack of cards to be sorted
Position stack1(pos_source[0]-100, pos_source[1], 0); // output stack: rares
Position stack2(pos_source[0]+50, pos_source[1], 0);  // output stack: bulk
Position stack3(pos_source[0]+100, pos_source[1], 0); // output stack: unidentified cards, tokens
Position stack4(0, pos_source[1]-105, 0); // output stack: basic lands

void setup(){
    Buzzer_init();
    ESPMax_init();
    Nozzle_init();
    // Serial.begin(921600);
    Serial.begin(9600);
    delay(3000);
    Serial.println("Reset to home...");
    go_home(2000); // 机械臂回到初始位置
    delay(3000);
    Serial.println("start...");
    // Pump_on();
    delay(400);
}

bool start_en = true;
void loop(){
    if (Serial.available() > 6) {
        String data = Serial.readStringUntil('\n');
        Serial.print("Recieved command: '");
        Serial.print(data);
        Serial.println("'");
        // if (data == "stack1") {
        //     Serial.println("Moving card to stack1");
        //     source.pick();
        //     stack1.place();
        // }
        // if (data == "stack2") {
        //     Serial.println("Moving card to stack2");
        //     source.pick();
        //     stack2.place();
        // }
        // if (data == "stack3") {
        //     Serial.println("Moving card to stack3");
        //     source.pick();
        //     stack3.place();
        // }
        // if (data == "stack4") {
        //     Serial.println("Moving card to stack4");
        //     source.pick();
        //     stack4.place();
        // }

        source.pick();
        stack1.place();
        go_home(2000);


    } else {
        delay(500); // 延时500毫秒
    }
}
