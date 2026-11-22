# Your Supply Chain Is a Spreadsheet Full of Guesses. It Should Be an Optimization Model.

*Six classic supply-chain decisions, built as exact models on a two-core box with open solvers and synthetic data whose answers I knew in advance. Stocking to the average demand lost money in every one. The warehouses came out about nine percent cheaper than the obvious layout, the safety stock dropped by two thirds at the same service level, and a customer who barely moved still made the factory swing ninety five times as hard.*

Most of the big decisions in a supply chain are made with a spreadsheet and a feeling. Where to put a warehouse, which one serves which region, how much of each product to hold, when to reorder. These are not small calls. They move more money than almost anything else a data scientist is allowed near, and they are usually settled by a round number, a manager's judgment, or a forecast dropped into a rule of thumb.

What bothers me about that is not that the answers are rough. It is that most of these decisions have an exact answer, and have had one for seventy years. Facility location, inventory under uncertainty, minimum-cost flow: these are among the most studied optimization problems there are, with open solvers that return the provably cheapest plan in seconds on a laptop. The gap between that plan and the guess is not a matter of taste. It is a fixed number of dollars, and you can compute it.

So I built the whole stack as optimization models and measured the gap every time. **Every scenario here is synthetic and seeded, so I know the true optimum and the true cost of the guess before I run anything.** No downloaded data, no GPU, nothing that needs more than two cores. The solvers are all open source, CBC and HiGHS through PuLP, so every number reproduces on a bare machine.

The forecast, by the way, is not the deliverable. **The forecast is the input. The decision it feeds is where the money is, and that decision is an optimization problem.** That sentence is the whole project.

## Start with the cheapest guess to disprove

Take the smallest inventory question there is. You stock one product for a season. Demand is uncertain. Every unit you do not sell is written off at a loss, call it the overage cost. Every unit you run short of is a lost sale, the underage cost. How many do you order?

Almost everyone orders the forecast. You expect to sell a hundred, so you stock a hundred. It feels careful. It is wrong, and it is wrong in a direction you can predict.

The right answer is the newsvendor model, and it is one line. The optimal stocking level is not the average demand. It is a specific percentile of the demand distribution, set by the ratio of the two costs:

```
optimal quantile = underage cost / (underage cost + overage cost)
```

If a stockout costs the same as a leftover, that ratio is one half and you stock the median, which for a symmetric distribution is the average. The moment the two costs differ, the quantile moves. In my setup a stockout costs three times a leftover, so the ratio is 0.75, and the model says stock the seventy fifth percentile of demand, not the fiftieth.

![Newsvendor optimum versus stocking to the mean](../outputs/figures/01_optimal_vs_mean.png)

*The demand curve with the two plans marked. Stocking to the mean sits at a hundred units. The newsvendor optimum sits at the seventy fifth percentile, about seventeen units higher, because running short is three times as painful as holding one spare.*

With a mean of a hundred units and a standard deviation of twenty five, the optimum lands near a hundred and seventeen. Seventeen extra units does not sound like much. But the expected cost of the two plans is not close. Stocking to the average runs about a quarter more expensive than the optimal order, season after season, for no reason other than habit.

And the gap is not a one-off. Push the cost of a stockout up relative to a leftover and it grows. Widen the demand distribution and it grows again, because the average becomes a worse stand-in for the right percentile the less certain you are.

![Cost of stocking to the mean as the cost ratio grows](../outputs/figures/01_gap_vs_cost_ratio.png)

*The money left on the table by stocking to the average, as the stockout cost climbs relative to the leftover cost. At parity the gap is zero. It opens from there and does not close.*

This is the same idea as picking a decision threshold for a classifier, where you move the cutoff because a false negative and a false positive do not cost the same. Here the asymmetric cost sets how much to order. Different problem, identical logic.

## Safety stock is not a round number

The newsvendor is a single season. Most products get reordered again and again, and the question shifts to the buffer: how much extra to carry so a bad week does not leave the shelf empty. That buffer is safety stock, and it is the most abused number in the warehouse.

The usual rule is a flat one. Two weeks of stock on everything. It is easy to say in a meeting and easy to defend, and it is wrong for almost every product at once. A steady staple with predictable demand gets the same buffer as a volatile seasonal item, so the staple drowns in stock it will never need while the volatile item still runs out.

The correct buffer is a formula, and it depends on the thing you already measure when you forecast: how much demand varies. In plain terms, the safety stock is the spread of demand times the square root of the lead time times a multiplier set by the service level you are targeting. More variable demand, more buffer. Longer wait for a refill, more buffer. Higher target for staying in stock, more buffer.

I took six products with the same average demand and very different volatility and set the buffer two ways. The flat rule gave each the same two weeks. The formula gave each what its own variability called for.

![Distribution-based safety stock versus a flat rule](../outputs/figures/02_safety_stock_by_product.png)

*Six products, one average demand, rising volatility left to right. The flat rule is the dashed line, identical for all. The formula sizes each buffer to the product, far below the flat line for the steady items and climbing only where the demand actually swings.*

Added up across the six products, the formula held about four hundred and twenty eight units of safety stock against the flat rule's twelve hundred. That is roughly two thirds less inventory. And it does not come at the cost of service. I checked the achieved service level by simulation, drawing demand over the lead time and counting how often the buffer held, and it matched the target to within a fifth of a percentage point. **Less inventory, same service, because the buffer moved off the products that never needed it and onto the ones that did.**

## Where to build, and what to expand

Now zoom out from one product to the whole network. You have a set of possible warehouse sites, each with a fixed cost to open and a limited capacity, and a set of customers with demand to serve. Which sites do you open, and who serves whom?

The intuitive version opens some sites and sends each customer to the nearest one. It reads well on a map. It also ignores the trade it is making, because the nearest site is not always the cheapest once you account for the fixed cost of keeping a site open and the fact that sites fill up.

The exact version is a mixed-integer program. The open-or-close choices are the integer part, the shipping quantities are the continuous part, and the objective is the total of fixed cost plus transport cost. An open solver returns the cheapest configuration and the exact assignment.

![The optimal warehouse network](../outputs/figures/03_network_map.png)

*The optimal network on a synthetic map. Open sites in orange, the closed candidate hollow, customers sized by demand. The lines show who each open site serves, thicker for more volume.*

On my instance the solver opened four of the five candidate sites. I checked that answer the slow, certain way, by listing every possible subset of sites to open and solving the shipping problem for each. The brute-force winner and the solver's answer matched to the cent, which is the point of keeping these instances small: you can prove the fast method is right.

Then I ran the nearest-site version for comparison.

![Optimized network versus nearest-site assignment](../outputs/figures/03_cost_vs_nearest_site.png)

*The optimized network against the nearest-site layout. Same customers, same candidate sites, about nine percent less total cost once the fixed costs and capacities are respected properly.*

The optimized plan came in about nine percent cheaper than nearest-site. That is money the map-reading version leaves on the floor, in a problem small enough to check by hand.

The solver hands you one more thing for free. Every capacity limit has a shadow price, the amount the total cost would drop if that one site had a single unit more capacity. Read those prices and you know which warehouse to expand next, and what the expansion is worth, before you spend anything. The plan and the strategy come out of the same model.

## The network is a flow problem

Opening sites is one half of network design. Moving product through the network is the other, and it is a linear program with an exact cheapest answer.

The basic form ships from sources to destinations at minimum cost, respecting how much each source can supply and how much each destination needs. Add a layer of warehouses in the middle and you get transshipment, where product flows from plants through warehouses to customers and the only extra rule is that whatever enters a warehouse has to leave it.

![Minimum-cost two-echelon flow](../outputs/figures/04_transshipment_network.png)

*A two-layer flow. Plants feed warehouses, warehouses feed customers, and the solver routes every unit at minimum total cost with flow conserved at each warehouse.*

I verified that conservation held at every node and that demand was met exactly, which it was. As with the facility problem, the dual values are worth as much as the flows. The shadow price on a customer's demand is what one more unit of sales there would cost to serve. The shadow price on a plant's supply is what one more unit of capacity there would save. Those are the numbers a network-design conversation actually turns on, and they fall out of the same solve.

## Where to hold the stock

Here is the result that caught me out the first time I saw it, and still feels slightly wrong until you do the arithmetic.

Suppose a distribution center supplies several stores, and each store holds its own safety stock. The intuitive move is to keep a buffer everywhere, close to the customer. The better move, often, is to pull that buffer back and pool it at the distribution center.

The reason is that independent demands do not add up the way their buffers do. The buffer you need scales with the spread of demand, and when you combine several independent streams the combined spread grows like the square root of the sum of squares, not the plain sum. Pool six stores and the pooled buffer is far smaller than the six separate ones added together.

![Decentralized versus pooled safety stock](../outputs/figures/05_decentralized_vs_centralized.png)

*The same six stores, the same target service level. A buffer at every store on the left, the pooled buffer at the distribution center on the right. Pooling cuts the total by well over half.*

In my six-store chain, buffers at every store came to about four hundred and twenty eight units. Pooled at the center, the same service level needed about a hundred and seventy nine. **You can take that saving as cash, holding far less inventory for the same availability, or spend it on a higher service level for the same inventory.** The benefit grows with the number of locations you pool, which is the whole argument for a central warehouse written as one equation.

## Why optimizing each piece is still not enough

Every section so far optimized one decision on its own. The last piece is about what happens when each stage of a chain optimizes locally and no one watches the whole thing.

It is the bullwhip effect, and it is easy to reproduce. I fed a chain of four stages a customer demand that barely moved, a steady average with a little noise. Each stage did something reasonable: forecast the orders coming from downstream, and reorder to keep a sensible buffer. Nothing malicious, nothing careless, just every stage minding its own position.

![Order-variance amplification by stage](../outputs/figures/06_amplification_by_stage.png)

*Order variability at each stage, measured against the customer. The customer is the baseline of one. Each stage upstream swings harder, and by the fourth the orders are about ninety five times as variable as the demand that started it all.*

The orders got wilder at every step upstream. By the fourth stage the order variability was about ninety five times that of the end customer. The factory at the top lurches between famine and flood while the shopper at the bottom buys the same amount every week. Each stage reacting only to its own incoming orders, with a forecast and a lead time in the loop, is enough to manufacture the chaos. The levers that calm it are the obvious ones once you see the cause: shorter lead times, more smoothing in the forecast, and above all sharing the real demand signal instead of letting each stage guess from the orders it happens to see.

## What it adds up to

Laid end to end, the supply chain stops looking like a run of judgment calls and starts looking like what it is, a stack of optimization problems. Each has an exact answer. Each answer beats the rule of thumb by an amount you can put a number on.

| Decision | The habit | The model | What it bought |
|---|---|---|---|
| Season stocking | order the forecast | newsvendor quantile | mean plan costs about 25 percent more |
| The buffer | flat two weeks | service-level formula | about two thirds less stock, same service |
| Where to build | nearest site | facility-location MILP | about 9 percent cheaper |
| How to route | manual lanes | minimum-cost flow | exact optimum, conservation checked |
| Where to hold stock | a buffer everywhere | pool upstream | over half the safety stock removed |
| The whole chain | optimize locally | share the signal | tames a 95x swing |

None of this needs a cluster or a commercial solver. It ran on two cores with open tools, on data small enough that I could check the optimizer against brute force and the formulas against simulation. That was the point. When you can see the true answer, you can see exactly how much the guess costs, and in supply chains the guess is rarely cheap.

The forecasting work most of us already do is the input to all of this. The decision it feeds is where the value shows up. If you can write that decision as an optimization model, you bring something most teams are still doing by hand.

The full code, the six notebooks, and every figure here live in the repository at [github.com/Dima806/supply_chain_arena](https://github.com/Dima806/supply_chain_arena). It builds on an earlier walk through mathematical optimization in [optimization_101](https://github.com/Dima806/optimization_101), and the asymmetric-cost idea behind the newsvendor is the same one I used for classification thresholds in [threshold_lab](https://github.com/Dima806/threshold_lab).
