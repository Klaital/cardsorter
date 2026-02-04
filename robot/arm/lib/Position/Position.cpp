//
// Created by Kit on 2/2/2026.
//

#include "Position.h"

#include <ESPMax.h>
#include <Arduino.h>
#include <SuctionNozzle.h>

void copy_pos(float src[3], float dst[3]) {
    for (int i=0; i<3; i++) {
        dst[i] = src[i];
    }
}

Position::Position(float x, float y, float starting_stack_height) {
    this->pos_base[0] = x;
    this->pos_base[1] = y;
    this->pos_base[2] = TABLE_HEIGHT;
    this->card_count = static_cast<int>(starting_stack_height / DEFAULT_CARD_THICKNESS); // this is now an estimate
}

void Position::go() {
    float pos[3];
    copy_pos(this->pos_base, pos);
    pos[2] = OVERHEAD_HEIGHT;
    set_position(pos, MOVEMENT_SPEED);
    delay(MOVEMENT_SPEED);
}

void Position::pick() {
    float pos[3];
    copy_pos(this->pos_base, pos);
    pos[2] = OVERHEAD_HEIGHT;
    set_position(pos, MOVEMENT_SPEED);
    delay(MOVEMENT_SPEED+MOVEMENT_LAG);
    pos[2] = TABLE_HEIGHT+(static_cast<float>(this->card_count)*DEFAULT_CARD_THICKNESS);
    set_position(pos, MOVEMENT_SPEED);
    delay(MOVEMENT_SPEED+MOVEMENT_LAG);
    Valve_off();
    if (this->card_count > 0) {
        this->card_count--;
    }
    delay(PICK_PUMP_LAG);
    pos[2] = OVERHEAD_HEIGHT;
    set_position(pos, MOVEMENT_SPEED);
    delay(MOVEMENT_SPEED+MOVEMENT_LAG);
}

void Position::place() {
    float pos[3];
    copy_pos(this->pos_base, pos);
    pos[2] = OVERHEAD_HEIGHT;
    set_position(pos, MOVEMENT_SPEED);
    delay(MOVEMENT_SPEED+MOVEMENT_LAG);
    pos[2] = TABLE_HEIGHT+(static_cast<float>(this->card_count)*DEFAULT_CARD_THICKNESS);
    set_position(pos, MOVEMENT_SPEED);
    delay(MOVEMENT_SPEED+MOVEMENT_LAG);
    Valve_on();
    this->card_count++;
    delay(PLACE_PUMP_LAG);
    pos[2] = OVERHEAD_HEIGHT;
    set_position(pos, MOVEMENT_SPEED);
    delay(MOVEMENT_SPEED+MOVEMENT_LAG);
}
