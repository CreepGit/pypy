package main

import (
	"fmt"
	"math"
)

func fnv1aHashIntBinary(num uint64) uint64 {
	// FNV constants for 32-bit hash
	const fnvPrime uint64 = 16777619
	const fnvOffsetBasis uint64 = 2166136261

	hash := fnvOffsetBasis

	// Process each byte of the integer
	for i := 0; i < 4; i++ {
		// Extract each byte of the integer
		b := byte((num >> (i * 8)) & 0xFF)
		// XOR the hash with the current byte
		hash ^= uint64(b)
		// Multiply by the prime
		hash *= fnvPrime
	}

	return hash
}

func isPrime(n uint) bool {
	if n <= 1 {
		return false
	}
	for i := uint(2); i*i <= n; i++ {
		if n%i == 0 {
			return false
		}
	}
	return true
}

func findPreviousPrime(n uint) uint {
	for i := n - 1; i > 1; i-- {
		if isPrime(i) {
			return i
		}
	}
	panic("No previous prime found")
}

type BloomFilter struct {
	bitArray  []uint64
	hashCount int
	size      uint64 // Total number of bits
}

var somePrimeOffset = findPreviousPrime(uint(math.Pow(2, 38)))

// hashResult represents a hash result with array index and bit position
type hashResult struct {
	arrayIndex uint64
	bitPos     uint64
}

func (b *BloomFilter) hashes(n uint64) []hashResult {
	results := make([]hashResult, b.hashCount)
	for i := 0; i < b.hashCount; i++ {
		hash := fnv1aHashIntBinary(uint64(n)*uint64((somePrimeOffset)*uint(i))) % b.size
		arrayIndex := hash / 64
		bitPos := hash % 64
		results[i] = hashResult{arrayIndex: arrayIndex, bitPos: bitPos}
	}
	return results
}

func (b *BloomFilter) Add(n uint64) {
	hashes := b.hashes(n)
	if b.containsHashes(hashes) {
		fmt.Println("Collision")
		return
	}
	for _, hash := range hashes {
		b.bitArray[hash.arrayIndex] |= (1 << hash.bitPos)
	}
}

func (b *BloomFilter) containsHashes(hashes []hashResult) bool {
	for _, hash := range hashes {
		if (b.bitArray[hash.arrayIndex] & (1 << hash.bitPos)) == 0 {
			return false
		}
	}
	return true
}

func (b *BloomFilter) Contains(n uint64) bool {
	hashes := b.hashes(n)
	return b.containsHashes(hashes)
}

type LCG struct {
	a uint
	m uint
	x uint
}

func (this *LCG) Next() uint {
	// c := 2^12 - 1
	c := uint(4095)
	this.x = (this.a*this.x + c) % this.m
	return this.x
}

type Result struct {
	iterations int
	percentage float64
	prime      uint
}

func findIterationSizeFor(poolSize uint, a uint, m uint, hashCount int) Result {
	// Calculate the number of uint64 elements needed
	arraySize := (poolSize + 63) / 64
	bf := BloomFilter{
		bitArray:  make([]uint64, arraySize),
		hashCount: hashCount,
		size:      uint64(poolSize),
	}
	lcg := LCG{a: a, m: m, x: 1}
	index := 0
	for {
		value := lcg.Next()
		if bf.Contains(uint64(value)) {
			return Result{
				iterations: index,
				percentage: float64(index) / float64(m),
			}
		}
		bf.Add(uint64(value))
		index++
	}
}

func numberToPoints(n uint) uint {
	nn := float64(n)
	points := uint(1)
	for nn > 1 {
		nn /= 1.2
		points++
	}
	return points - 50
}

func findGoodAAndM(poolSize uint, targetSize uint, hashCount int) (uint, uint, float64) {
	goodAValues := []uint{214013, 69069, 48271, 16807, 22695477, 3263443, 465019, 481621, 456979}
	mValues := make([]uint, 4)
	lastNum := targetSize
	best := struct {
		a          uint
		m          uint
		percentage float64
		iterations int
	}{}
	for i := 0; i < len(mValues); i++ {
		lastNum = findPreviousPrime(lastNum)
		mValues[i] = lastNum
	}
	for _, a := range goodAValues {
		for _, m := range mValues {
			result := findIterationSizeFor(poolSize, a, m, hashCount)
			fmt.Printf("%.2f%% %dpts %d\n", result.percentage*100, numberToPoints(uint(result.iterations)), result.iterations)
			if result.percentage > 0.95 {
				return a, m, result.percentage
			}
			if result.iterations > best.iterations {
				best = struct {
					a          uint
					m          uint
					percentage float64
					iterations int
				}{
					a:          a,
					m:          m,
					percentage: result.percentage,
					iterations: result.iterations,
				}
			}
		}
		fmt.Println(a)
		fmt.Println("--------------------------------")
	}
	return best.a, best.m, best.percentage
}

type Target struct {
	size    uint
	display string
}

func main() {
	bigPool := uint(4294967296) * 8
	targetSizes := []Target{
		// {uint(math.Pow(52, 2)), "52^2"},
		// {uint(math.Pow(62, 2)), "62^2"},
		// {uint(math.Pow(52, 3)), "52^3"},
		// {uint(math.Pow(62, 3)), "62^3"},
		// {uint(math.Pow(52, 4)), "52^4"},
		// {uint(math.Pow(62, 4)), "62^4"},
		{uint(math.Pow(52, 5)), "52^5"},
		// {uint(math.Pow(62, 5)), "62^5"},
	}
	for _, target := range targetSizes {
		fmt.Printf("Looking at: %s (%d)s\n", target.display, target.size)
		a, m, percentage := findGoodAAndM(bigPool, target.size, 40)
		fmt.Printf("a: %d, m: %d, %.2f%%\n\n", a, m, percentage*100)
	}
}
