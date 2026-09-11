#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "golden_vectors_v1.h"

#define HEADER_SIZE 10u
#define CRC_SIZE 2u

static uint16_t read_u16_le(const uint8_t *data) {
  return (uint16_t)((uint16_t)data[0] | ((uint16_t)data[1] << 8u));
}

static uint16_t crc16_ccitt_false(const uint8_t *data, size_t length) {
  uint16_t crc = 0xffffu;
  size_t index;

  for (index = 0u; index < length; ++index) {
    uint8_t bit;
    crc ^= (uint16_t)((uint16_t)data[index] << 8u);
    for (bit = 0u; bit < 8u; ++bit) {
      crc = (crc & 0x8000u) != 0u
                ? (uint16_t)((crc << 1u) ^ 0x1021u)
                : (uint16_t)(crc << 1u);
    }
  }
  return crc;
}

static int verify_vector(const oomwoo_golden_vector_t *vector) {
  const uint8_t *frame = vector->frame;
  const size_t expected_length = HEADER_SIZE + vector->payload_length + CRC_SIZE;
  uint16_t expected_crc;
  uint16_t actual_crc;

  if (vector->frame_length != expected_length || frame[0] != (uint8_t)'O' ||
      frame[1] != (uint8_t)'W' || frame[2] != 1u ||
      frame[3] != vector->flags || read_u16_le(frame + 4u) != vector->sequence ||
      read_u16_le(frame + 6u) != vector->message_type ||
      read_u16_le(frame + 8u) != vector->payload_length ||
      memcmp(frame + HEADER_SIZE, vector->payload, vector->payload_length) != 0) {
    fprintf(stderr, "header/payload mismatch: %s\n", vector->name);
    return 1;
  }

  expected_crc = read_u16_le(frame + vector->frame_length - CRC_SIZE);
  actual_crc = crc16_ccitt_false(frame, vector->frame_length - CRC_SIZE);
  if (expected_crc != actual_crc) {
    fprintf(stderr, "CRC mismatch: %s\n", vector->name);
    return 1;
  }
  return 0;
}

int main(void) {
  size_t index;

  for (index = 0u; index < OOMWOO_GOLDEN_VECTOR_COUNT; ++index) {
    if (verify_vector(&oomwoo_golden_vectors[index]) != 0) {
      return 1;
    }
  }
  printf("OOMWOO protocol v1: %zu golden vectors PASS\n",
         (size_t)OOMWOO_GOLDEN_VECTOR_COUNT);
  return 0;
}
