#ifndef IAWARE_SAMPLING_DATA_H
#define IAWARE_SAMPLING_DATA_H

// #define SAMPLING_DATA_FS 30000	// Default sampling frequency
#define SAMPLING_DATA_FS 20000	// Default sampling frequency
// #define SAMPLING_DATA_FS 1000	// Default sampling frequency
// #define SAMPLING_DATA_FS 2000	// Default sampling frequency
// #define SAMPLING_DATA_FS 2	// Default sampling frequency

extern uint32_t sampling_data_fs;	// The sampling frequency of the signal.

void init_sampling_data_task(void);
void sampling_data_createTimer(void);
void sampling_data_startTimer(int64_t duration);
void sampling_data_stopTimer(void);

void init_buff_nodes(void);

#endif