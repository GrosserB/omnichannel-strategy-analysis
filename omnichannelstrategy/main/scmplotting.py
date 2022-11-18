import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from SyntheticControlMethods import Synth
from SyntheticControlMethods.main import SynthBase

# Class from SyntheticControlMethod altered to return the Figure of the Plot (everything else untouched)
class CustomPlot(object):
    '''This class is responsible for all plotting functionality'''

    def custom_plot(self,
            panels,
            figsize=(15, 12),
            treated_label="Treated Unit",
            synth_label="Synthetic Treated Unit",
            treatment_label="Treatment",
            in_space_exclusion_multiple=5):

        data = self.original_data

        #Extract Synthetic Control
        synth = data.synth_outcome
        ### NOTICE ###
        time = data.dataset[data.time].unique().to_numpy
        ### plot function has problems with this being a pandas array, so we convert it into numpy array (2022/11/17)

        plt = self._get_plotter()
        fig = plt.figure(figsize=figsize)
        valid_panels = ['original', 'pointwise', 'cumulative',
                        'in-space placebo', 'rmspe ratio', 'in-time placebo']
        solo_panels = ['rmspe ratio'] #plots with different axes
        for panel in panels:
            if panel not in valid_panels:
                raise ValueError(
                    '"{}" is not a valid panel. Valid panels are: {}.'.format(
                        panel, ', '.join(['"{}"'.format(e) for e in valid_panels])
                    )
                )
            if panel in solo_panels and len(panels) > 1:
                print("{} is meant to have a different x-axis, plotting it together with other plots may hide that").format(panel)
                #warning.warn('Validity plots should be plotted alone', PlotWarning)


        n_panels = len(panels)
        ax = plt.subplot(n_panels, 1, 1)
        idx = 1

        if 'original' in panels:
            #Determine appropriate limits for y-axis
            max_value = max(np.max(data.treated_outcome_all),
                            np.max(data.synth_outcome))
            min_value = min(np.min(data.treated_outcome_all),
                            np.min(data.synth_outcome))

            #Make plot
            ax.set_title("{} vs. {}".format(treated_label, synth_label))
            ax.plot(time, synth.T, 'r--', label=synth_label)
            ax.plot(time ,data.treated_outcome_all, 'b-', label=treated_label)
            ax.axvline(data.treatment_period-1, linestyle=':', color="gray")
            ax.set_ylim(-1.2*abs(min_value), 1.2*abs(max_value)) #Do abs() in case min is positive, or max is negative
            ax.annotate(treatment_label,
                #Put label below outcome if pre-treatment trajectory is decreasing, else above
                xy=(data.treatment_period-1, data.treated_outcome[-1]*(1 + 0.2*np.sign(data.treated_outcome[-1] - data.treated_outcome[0]))),
                xytext=(-160, -4),
                xycoords='data',
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))
            ax.set_ylabel(data.outcome_var)
            ax.set_xlabel(data.time)
            ax.legend()

            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        if 'pointwise' in panels:

            ax = plt.subplot(n_panels, 1, idx, sharex=ax)
            #Subtract outcome of synth from both synth and treated outcome
            normalized_treated_outcome = data.treated_outcome_all - synth.T
            normalized_synth = np.zeros(data.periods_all)
            most_extreme_value = np.max(np.absolute(normalized_treated_outcome))

            ax.set_title("Pointwise Effects")
            ax.plot(time, normalized_synth, 'r--', label=synth_label)
            ax.plot(time ,normalized_treated_outcome, 'b-', label=treated_label)
            ax.axvline(data.treatment_period-1, linestyle=':', color="gray")
            ax.set_ylim(-1.2*most_extreme_value, 1.2*most_extreme_value)
            ax.annotate(treatment_label,
                xy=(data.treatment_period-1, 0.5*most_extreme_value),
                xycoords='data',
                xytext=(-160, -4),
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))
            ax.set_ylabel(data.outcome_var)
            ax.set_xlabel(data.time)
            ax.legend()

            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        if 'cumulative' in panels:
            ax = plt.subplot(n_panels, 1, idx, sharex=ax)
            #Compute cumulative treatment effect as cumulative sum of pointwise effects
            cumulative_effect = np.cumsum(normalized_treated_outcome[data.periods_pre_treatment:])
            cummulative_treated_outcome = np.concatenate((np.zeros(data.periods_pre_treatment), cumulative_effect), axis=None)
            normalized_synth = np.zeros(data.periods_all)

            ax.set_title("Cumulative Effects")
            ax.plot(time, normalized_synth, 'r--', label=synth_label)
            ax.plot(time ,cummulative_treated_outcome, 'b-', label=treated_label)
            ax.axvline(data.treatment_period-1, linestyle=':', color="gray")
            #ax.set_ylim(-1.1*most_extreme_value, 1.1*most_extreme_value)
            ax.annotate(treatment_label,
                xy=(data.treatment_period-1, cummulative_treated_outcome[-1]*0.3),
                xycoords='data',
                xytext=(-160, -4),
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))
            ax.set_ylabel(data.outcome_var)
            ax.set_xlabel(data.time)
            ax.legend()

            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        if 'in-space placebo' in panels:
            #assert self.in_space_placebos != None, "Must run in_space_placebo() before you can plot!"

            ax = plt.subplot(n_panels, 1, idx)
            zero_line = np.zeros(data.periods_all)
            normalized_treated_outcome = data.treated_outcome_all - synth.T

            ax.set_title("In-space placebo's")
            ax.plot(time, zero_line, 'k--')

            #Plot each placebo
            ax.plot(time, data.in_space_placebos[0], ('0.7'), label="Placebos")
            for i in range(1, data.n_controls):

                #If the pre rmspe is not more than
                #in_space_exclusion_multiple times larger than synth pre rmspe
                if in_space_exclusion_multiple is not None:
                  if data.rmspe_df["pre_rmspe"].iloc[i] < in_space_exclusion_multiple*data.rmspe_df["pre_rmspe"].iloc[0]:
                      ax.plot(time, data.in_space_placebos[i], ('0.7'))
                else:
                  ax.plot(time, data.in_space_placebos[i], ('0.7'))

            ax.axvline(data.treatment_period-1, linestyle=':', color="gray")
            ax.plot(time, normalized_treated_outcome, 'b-', label=treated_label)

            ax.set_ylabel(data.outcome_var)
            ax.set_xlabel(data.time)
            ax.legend()

            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        if 'rmspe ratio' in panels:
            assert data.rmspe_df.shape[0] != 1, "Must run in_space_placebo() before you can plot 'rmspe ratio'!"

            #Sort by post/pre rmspe ratio, high
            sorted_rmspe_df = data.rmspe_df.sort_values(by=["post/pre"], axis=0, ascending=True)

            ax = plt.subplot(n_panels, 1, idx)
            ax.set_title("Postperiod RMSPE / Preperiod RMSPE")


            #Create horizontal barplot, one bar per unit
            y_pos = np.arange(data.n_controls+1) #Number of units
            ax.barh(y_pos, sorted_rmspe_df["post/pre"],
                     color="#3F5D7D",  ec="black")

            #Label bars with unit names
            ax.set_yticks(y_pos)
            ax.set_yticklabels(sorted_rmspe_df["unit"])

            #Label x-axis
            ax.set_xlabel("Postperiod RMSPE / Preperiod RMSPE")

            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        if 'in-time placebo' in panels:

            ax = plt.subplot(n_panels, 1, idx)
            ax.set_title("In-time placebo: {} vs. {}".format(treated_label, synth_label))

            ax.plot(time, data.in_time_placebo_outcome.T, 'r--', label=synth_label)
            ax.plot(time, data.treated_outcome_all, 'b-', label=treated_label)

            ax.axvline(data.placebo_treatment_period, linestyle=':', color="gray")
            ax.annotate('Placebo Treatment',
                xy=(data.placebo_treatment_period, data.treated_outcome_all[data.placebo_periods_pre_treatment]*1.2),
                xytext=(-160, -4),
                xycoords='data',
                textcoords='offset points',

                arrowprops=dict(arrowstyle="->"))
            ax.set_ylabel(data.outcome_var)
            ax.set_xlabel(data.time)
            ax.legend()

            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        fig.tight_layout(pad=3.0)

        # only correction to make the plot accessable after plotting
        #plt.show()

        return fig


class CustomSynth(CustomPlot, Synth):

  def __init__(self, dataset,
            outcome_var, id_var, time_var,
            treatment_period, treated_unit,
            n_optim=10, pen=0, exclude_columns=[], random_seed=0,
            **kwargs):

    self.method = "SC"

    original_checked_input = self._process_input_data(
        dataset, outcome_var, id_var, time_var, treatment_period, treated_unit, pen,
        exclude_columns, random_seed, **kwargs
    )
    self.original_data = SynthBase(**original_checked_input)

    #Get synthetic Control
    self.optimize(self.original_data.treated_outcome, self.original_data.treated_covariates,
                self.original_data.control_outcome, self.original_data.control_covariates,
                self.original_data.pairwise_difference,
                self.original_data, False, pen, n_optim)

    #Compute rmspe_df
    self._pre_post_rmspe_ratios(None, False)

    #Prepare weight_df with unit weights
    self.original_data.weight_df = self._get_weight_df(self.original_data)
    self.original_data.comparison_df = self._get_comparison_df(self.original_data)


def beautify_scm_plot(fig,
                      df_stores: pd.DataFrame,
                      treatment_area: str,
                      title: str="",
                      before_quarter: int=12,
                      after_quarter: int=12):

  df_stores['opening_year_quarter'] = pd.PeriodIndex(df_stores.opening_year_quarter, freq='Q')

  fig.set_size_inches((20,8))
  ax = fig.gca()
  if title == "":
    title = f'{treatment_area} vs Synthetic {treatment_area}'

  ax.set_title(title, fontsize=30);
  ax.set_xlabel("", fontsize=0);
  ax.set_ylabel("Average Order Value per Postal Code Area (in EUR)", fontsize='15');

  xticks_all = [(df_stores.loc[treatment_area].opening_year_quarter - before_quarter + x, x) for x in range((before_quarter+after_quarter+1))]
  xticks_years = [xtick for xtick in xticks_all if str(xtick[0]).endswith("Q1")]

  ax.set_xticks(ticks=[xtick[1] for xtick in xticks_years], minor=False);
  ax.set_xticklabels(labels=[str(xtick[0])[:-2]for xtick in xticks_years], minor=False);

  yticks = [int(ytick) for ytick in ax.get_yticks() if ytick >= 0]
  ytick_labels = [f"EUR {str(ytick)[:-3]},{str(ytick)[-3:]}" if ytick >= 1000 else f"EUR {str(ytick)}" for ytick in yticks]

  #ax.set_yticks(yticks[:-1]);
  ax.set_yticks(yticks);
  ax.set_yticklabels(ytick_labels);
