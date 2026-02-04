//
// Created by Kit on 2/2/2026.
//

#ifndef POSITION_H
#define POSITION_H

#define MOVEMENT_SPEED 500
#define MOVEMENT_LAG 1000
#define PICK_PUMP_LAG 400
#define PLACE_PUMP_LAG 300


void copy_pos(float src[3], float dst[3]);
#define OVERHEAD_HEIGHT 200
#define TABLE_HEIGHT 56.8
constexpr float DEFAULT_CARD_THICKNESS = 0.3f; // 0.3 to 0.32 mm thickness for Magic cards.

class Position {
public:
    // Coordinates of the center of the cards on the table (bottom of the stack)
    // Number of cards on this stack determines the place height
    float pos_base[3]{};
    int card_count = 0;

    Position(float x, float y, float starting_stack_height);

    void go(); // move to the overhead position
    void pick(); // move to the top of the cardstack and turn the pump on
    void place(); // move to the top of the cardstack and turn the pump off
};



#endif //POSITION_H
