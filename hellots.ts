
console.log("Hello typescript!")

interface ImplementsHello {
    hello(): string;
    greeting: string;
}

interface ImplementsSorry {
    sorry(): string;
}

class Hello implements ImplementsHello, ImplementsSorry {
    greeting: string;

    constructor(message: string) {
        this.greeting = message;
    }

    hello() {
        return "Hello " + this.greeting;
    }

    sorry() {
        return "I'm sorry";
    }
}


const hello = new Hello("World");
console.log(hello.hello())
console.log(hello.sorry())


const smth: any = hello
const smth2: ImplementsHello = smth
console.log(smth2.hello())
