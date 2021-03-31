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
package aztech.modern_industrialization.transferapi;

import alexiil.mc.lib.attributes.Simulation;
import alexiil.mc.lib.attributes.fluid.FluidExtractable;
import alexiil.mc.lib.attributes.fluid.FluidInsertable;
import alexiil.mc.lib.attributes.fluid.amount.FluidAmount;
import alexiil.mc.lib.attributes.fluid.volume.FluidKeys;
import java.math.RoundingMode;
import net.minecraft.fluid.Fluid;
import net.minecraft.fluid.Fluids;

/**
 * Because LBA is annoying to work with.
 */
public class FluidTransferHelper {
    /**
     * Similar to
     * {@link net.fabricmc.fabric.api.transfer.v1.storage.Storage#insert}.
     */
    public static long insert(FluidInsertable insertable, Fluid fluid, long amount) {
        FluidAmount fractionAmount = FluidAmount.of(amount, 81000);
        long leftover = insertable.insert(FluidKeys.get(fluid).withAmount(fractionAmount)).getAmount_F().asLong(81000, RoundingMode.DOWN);
        return amount - leftover;
    }

    /**
     * Return an extractable fluid, or EMPTY if none could be found.
     */
    public static Fluid findExtractableFluid(FluidExtractable extractable) {
        return extractable
                .attemptExtraction(key -> key.getRawFluid() != null && key.getRawFluid() != Fluids.EMPTY, FluidAmount.A_MILLION, Simulation.SIMULATE)
                .getRawFluid();
    }

    /**
     * Similar to
     * {@link net.fabricmc.fabric.api.transfer.v1.storage.Storage#extract}.
     */
    public static long extract(FluidExtractable extractable, Fluid fluid, long amount) {
        return extractable.extract(key -> key.getRawFluid() == fluid, FluidAmount.of(amount, 81000)).amount().asLong(81000, RoundingMode.DOWN);
    }
}