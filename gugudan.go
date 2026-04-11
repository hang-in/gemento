package main

import "fmt"

func main() {
	for i := 2; i <= 9; i++ {
		for j := 1; j <= 9; j++ {
			fmt.Printf("%d x %d = %d\n", i, j, i*j)
		}
		fmt.Println()
	}
}
