import java.util.List;

public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }

    public int calculateTotal(List<Integer> numbers) {
        int sum = 0;
        for (int n : numbers) {
            sum = add(sum, n);
        }
        return sum;
    }
}
