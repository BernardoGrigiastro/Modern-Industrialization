/*
 * MIT License
 *
 * Copyright (c) 2020 Azercoco & Technici4n
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
package aztech.modern_industrialization.inventory;

import java.util.ArrayList;
import net.minecraft.network.PacketByteBuf;

public class SlotPositions {
    private final int[] x, y;

    private SlotPositions(int[] x, int[] y) {
        this.x = x;
        this.y = y;
    }

    public int getX(int index) {
        return x[index];
    }

    public int getY(int index) {
        return y[index];
    }

    public int size() {
        return x.length;
    }

    public void write(PacketByteBuf buf) {
        buf.writeIntArray(x);
        buf.writeIntArray(y);
    }

    public static SlotPositions read(PacketByteBuf buf) {
        int[] x = buf.readIntArray();
        int[] y = buf.readIntArray();
        return new SlotPositions(x, y);
    }

    public static SlotPositions empty() {
        return new SlotPositions(new int[0], new int[0]);
    }

    public static class Builder {
        private final ArrayList<Integer> x = new ArrayList<>();
        private final ArrayList<Integer> y = new ArrayList<>();

        public Builder addSlot(int x, int y) {
            this.x.add(x);
            this.y.add(y);
            return this;
        }

        public Builder addSlots(int x, int y, int rows, int columns) {
            for (int i = 0; i < rows; ++i) {
                for (int j = 0; j < columns; ++j) {
                    addSlot(x + i * 18, y + j * 18);
                }
            }
            return this;
        }

        public SlotPositions build() {
            return new SlotPositions(x.stream().mapToInt(x -> x).toArray(), y.stream().mapToInt(y -> y).toArray());
        }
    }
}