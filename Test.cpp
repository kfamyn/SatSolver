#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include <fstream>
#include <string>
#include <dirent.h>

const int timeoutTime = 5;

const enum  SIGNS { POSITIVE = 0, NEGATIVE = 1 };
const short ASCII_TO_ALPHABETICAL = 97;
const short ALPHABET_LENGTH = 26;
const short MAX_LINES = 256;

void printMachineWord(int word);


void read(const std::string& filename)
{


	// ||||
	// VVVV
	// TODO: Your code for reading files
	// ...


	std::ifstream file(filename);
	if (file.is_open()) {
		std::string line;
		while (std::getline(file, line)) {
			// Process each line in the file
			// ...
		}
		file.close();
	}
	else {
		std::cerr << "Failed to open file: " << filename << std::endl;
	}
}



void find(const std::string& filename)
{
	std::ifstream CNF;
	std::string CNFLine;
	std::vector<int> literalSigns(MAX_LINES, 0);
	std::vector<int> literalExists(MAX_LINES, 0);
	short lineCount = 0;
	CNF.open(filename);
	if (CNF.is_open()) {
		while (std::getline(CNF, CNFLine))
		{
			bool sign = POSITIVE;
			for (size_t i = 0; i < CNFLine.length(); ++i)
			{
				if (CNFLine[i] != '_') {
					int mask = 1;
					mask = mask << (CNFLine[i] - ASCII_TO_ALPHABETICAL);
					literalExists[lineCount] |= mask;
					if (sign == NEGATIVE) {
						literalSigns[lineCount] |= mask;
					}
				}
				else sign = NEGATIVE;
			}
			++lineCount;
		}
		CNF.close();
	}
	else {
		std::cout << "Unable to open file";
	}
	int only26LastSymbols = 1;
	for (size_t i = 0; i < ALPHABET_LENGTH - 1; i++)
	{
		only26LastSymbols = only26LastSymbols << 1;
		++only26LastSymbols;
	}
	for (size_t line = 0; line < lineCount; ++line)
	{
		literalExists[line] = literalExists[line] & only26LastSymbols;
	}
	int solutionAttempt = 1;
	int solution = 0;
	while (!solution) {
		solution = 1;
		for (size_t line = 0; line < lineCount; ++line)
		{
			if ((literalSigns[line] ^ solutionAttempt & literalExists[line]) == 0) {
				solution = 0;
				break;
			}
		}
		if (solution != 0) {
			solution = solutionAttempt;
			//std::cout << filename << " SAT: \n";
			//printMachineWord(solution);
			//std::cout << std::endl;
		}
		else {
			++solutionAttempt;
		}
	}
}



void findTimeout(const std::string& filename)
{
	std::thread t([&]()
		{
			try
			{
				find(filename);
			}
			catch (const std::exception& e)
			{
				std::cerr << e.what() << std::endl;
			}
		});

	t.joinable();
	t.join();
}



int main()
{
	std::string folderPath = "./tests";
	std::vector<double> times;

	DIR* dir;
	struct dirent* entry;
	if ((dir = opendir(folderPath.c_str())) != nullptr)
	{
		while ((entry = readdir(dir)) != nullptr)
		{
			std::string filename = entry->d_name;
			if (filename != "." && filename != "..")
			{
				std::string filePath = folderPath + "/" + filename;
				auto startTime = std::chrono::high_resolution_clock::now();

				try
				{
					findTimeout(filePath);
				}
				catch (const std::exception& e)
				{
					std::cerr << e.what() << std::endl;
				}
				auto endTime = std::chrono::high_resolution_clock::now();
				double duration = std::chrono::duration_cast<std::chrono::nanoseconds>(endTime - startTime).count() / 1000000000.0;
				times.push_back(duration);
			}
		}
		closedir(dir);
	}
	else
	{
		std::cerr << "Failed to open directory: " << folderPath << std::endl;
		return 1;
	}



	// Printing the result
	std::cout << std::scientific;
	for (double time : times)
	{
		if (time < timeoutTime)
		{
			std::cout << time << " ";
		}
		else
		{
			std::cout << "inf ";
		}
	}
	return 0;
}

void printMachineWord(int word) {
	int mask = 1;
	for (size_t bit = 0; bit < ALPHABET_LENGTH; ++bit)
	{
		std::cout << ((word & mask) != 0) << " ";
		mask = mask << 1;
	}
}